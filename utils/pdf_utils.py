# -*- coding: utf-8 -*-
"""
見積書作成システム - PDF生成ユーティリティ
ExcelファイルをPDFに変換する機能を提供
"""

import subprocess
from pathlib import Path

# グローバルなアプリケーション参照（外部から渡される）
app = None


def set_app_context(flask_app):
    """
    Flask アプリケーションコンテキストを設定

    Args:
        flask_app: Flask アプリケーションインスタンス
    """
    global app
    app = flask_app


def generate_pdf_from_excel(excel_files, output_folder):
    """
    ExcelファイルをPDFに変換して保存

    Args:
        excel_files: Excel ファイルパスのリスト
        output_folder: 出力フォルダ

    Returns:
        {'success': bool, 'files': [生成したPDFファイル名], 'failed': [失敗したファイル名], 'message': str}
    """
    try:
        output_path = Path(output_folder)

        if not output_path.exists():
            return {
                'success': False,
                'files': [],
                'failed': [],
                'message': f'エラー：フォルダが見つかりません：{output_folder}'
            }

        if app:
            app.logger.info(f'PDF生成を開始: {output_folder}')

        if not excel_files:
            return {
                'success': False,
                'files': [],
                'failed': [],
                'message': 'エラー：生成対象のExcelファイルが指定されていません'
            }

        # ファイルパスを完全パスに変換
        excel_file_paths = [str(output_path / f) if not Path(f).is_absolute() else f for f in excel_files]

        if app:
            app.logger.info(f'PDF変換対象ファイル: {excel_file_paths}')

        if not excel_file_paths:
            return {
                'success': False,
                'files': [],
                'failed': [],
                'message': 'エラー：見積書ファイル（見積書_*.xlsx）が見つかりません'
            }

        if app:
            app.logger.info(f'PDF変換対象ファイル数: {len(excel_file_paths)}')

        generated_pdfs = []
        failed_files = []

        for excel_file in excel_file_paths:
            try:
                if app:
                    app.logger.info(f'PDF変換中: {Path(excel_file).name}')

                # LibreOffice のパスを探す
                libreoffice_paths = [
                    r'C:\Program Files\LibreOffice\program\soffice.exe',
                    r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
                    'libreoffice',  # PATH に登録されている場合
                ]

                libreoffice_exe = None
                for path in libreoffice_paths:
                    if Path(path).exists() or path == 'libreoffice':
                        libreoffice_exe = path
                        break

                if not libreoffice_exe:
                    if app:
                        app.logger.error('LibreOffice が見つかりません')
                    return {
                        'success': False,
                        'files': generated_pdfs,
                        'failed': failed_files + [Path(excel_file).name],
                        'message': 'エラー：LibreOffice がインストールされていません。標準的なインストール場所を確認してください'
                    }

                # LibreOffice コマンドラインで PDF に変換
                # Windows: soffice.exe --headless --convert-to pdf --outdir "folder" "file"
                try:
                    result = subprocess.run(
                        [
                            libreoffice_exe,
                            '--headless',
                            '--convert-to', 'pdf',
                            '--outdir', str(output_path),
                            excel_file
                        ],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode == 0:
                        # PDF ファイル名を生成（.xlsx を .pdf に置換）
                        pdf_name = Path(excel_file).stem + '.pdf'
                        pdf_path = output_path / pdf_name

                        if pdf_path.exists():
                            if app:
                                app.logger.info(f'✅ PDF生成完了: {pdf_name}')
                            generated_pdfs.append(pdf_name)
                        else:
                            if app:
                                app.logger.warning(f'❌ PDFファイルが見つかりません: {pdf_path}')
                            failed_files.append(Path(excel_file).name)
                    else:
                        if app:
                            app.logger.warning(f'LibreOffice 変換エラー: {result.stderr}')
                        failed_files.append(Path(excel_file).name)

                except FileNotFoundError:
                    if app:
                        app.logger.error('LibreOffice がインストールされていません')
                    return {
                        'success': False,
                        'files': generated_pdfs,
                        'failed': failed_files + [Path(excel_file).name],
                        'message': 'エラー：LibreOffice がインストールされていません。PDF変換にはLibreOfficeが必要です'
                    }

                except subprocess.TimeoutExpired:
                    if app:
                        app.logger.error(f'PDF変換タイムアウト: {Path(excel_file).name}')
                    failed_files.append(Path(excel_file).name)

            except Exception as file_error:
                if app:
                    app.logger.error(f'PDF変換エラー（{Path(excel_file).name}）: {file_error}')
                failed_files.append(Path(excel_file).name)

        if not generated_pdfs:
            return {
                'success': False,
                'files': [],
                'failed': failed_files,
                'message': 'エラー：PDFファイルの生成に失敗しました'
            }

        message = f'{len(generated_pdfs)}件のPDFファイルを生成しました'
        if failed_files:
            message += f'\n\n⚠️ 変換失敗: {", ".join(failed_files)}'

        if app:
            app.logger.info(f'PDF生成完了: {message}')

        return {
            'success': True,
            'files': generated_pdfs,
            'failed': failed_files,
            'message': message
        }

    except Exception as error:
        if app:
            app.logger.error(f'PDF生成エラー: {error}')
        import traceback
        if app:
            app.logger.error(traceback.format_exc())
        return {
            'success': False,
            'files': [],
            'failed': [],
            'message': f'PDF生成エラー：{str(error)}'
        }
