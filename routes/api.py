# -*- coding: utf-8 -*-
"""
見積書作成システム - API エンドポイント
REST API ルートを定義
"""

import uuid
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from flask import request, jsonify

from utils.excel_utils import write_to_excel, check_excel_macros, generate_estimate_sheets
from utils.pdf_utils import generate_pdf_from_excel
from utils.drive_utils import (
    is_google_drive_path, parse_google_drive_path,
    download_file_from_drive, find_file_id_by_name,
    find_folder_id_by_name, upload_file_to_drive
)

# グローバルなアプリケーション参照（外部から渡される）
app = None
estimate_data = None


def register_api_routes(flask_app, estimate_data_dict):
    """
    API ルートを登録

    Args:
        flask_app: Flask アプリケーションインスタンス
        estimate_data_dict: 見積データを格納するメモリ辞書
    """
    global app, estimate_data
    app = flask_app
    estimate_data = estimate_data_dict

    @app.route('/api/write-content', methods=['POST'])
    def write_content():
        """
        ステップ①：見積内容を保存（Excelファイルに書き込み）
        """
        try:
            data = request.get_json()
            rows = data.get('rows', [])
            management_file = data.get('managementFile', '')
            price_list = data.get('priceList', '')

            # ファイルパス入力チェック
            if not management_file or not price_list:
                return jsonify({
                    'success': False,
                    'message': 'エラー：管理ファイルと金額リストの両方を指定してください'
                }), 400

            # ローカルパス / Google Drive パスの判定と取得
            app.logger.info(f'管理ファイル: {management_file}')
            app.logger.info(f'金額リスト: {price_list}')

            # 管理ファイルを取得
            mgmt_local_path = None
            try:
                if is_google_drive_path(management_file):
                    # Google Drive パスの場合
                    app.logger.info('管理ファイルは Google Drive パス')
                    mgmt_parsed = parse_google_drive_path(management_file)

                    try:
                        if mgmt_parsed['type'] == 'folder_id':
                            # フォルダ ID で指定
                            file_id = find_file_id_by_name('請求書＆注文書生成_双日用_Excel版2.xlsx', mgmt_parsed['folder_id'])
                            if not file_id:
                                raise Exception('ファイルが見つかりません')
                        else:
                            # gdrive://folder/file 形式
                            folder_id = find_folder_id_by_name(mgmt_parsed['folder_name'])
                            file_id = find_file_id_by_name(mgmt_parsed['file_name'], folder_id)
                            if not file_id:
                                raise Exception('ファイルが見つかりません')

                        # 一時ファイルに保存
                        mgmt_local_path = os.path.join(tempfile.gettempdir(), f'mgmt_{uuid.uuid4()}.xlsx')
                        download_file_from_drive(file_id, mgmt_local_path)
                        app.logger.info(f'管理ファイルをダウンロード: {mgmt_local_path}')

                    except Exception as drive_error:
                        app.logger.error(f'Google Drive アクセスエラー: {drive_error}')
                        return jsonify({
                            'success': False,
                            'message': f'エラー：Google Drive ファイルにアクセスできません\n{str(drive_error)}'
                        }), 400
                else:
                    # ローカルパスの場合
                    app.logger.info('管理ファイルはローカルパス')
                    mgmt_path = Path(management_file)
                    if not mgmt_path.exists():
                        return jsonify({
                            'success': False,
                            'message': f'エラー：管理ファイルが見つかりません\n{management_file}'
                        }), 400
                    mgmt_local_path = str(mgmt_path)

            except Exception as e:
                app.logger.error(f'管理ファイル取得エラー: {e}')
                return jsonify({
                    'success': False,
                    'message': f'エラー：管理ファイルの取得に失敗しました\n{str(e)}'
                }), 400

            # 金額リストを取得
            price_local_path = None
            try:
                if is_google_drive_path(price_list):
                    # Google Drive パスの場合
                    app.logger.info('金額リストは Google Drive パス')
                    price_parsed = parse_google_drive_path(price_list)

                    try:
                        if price_parsed['type'] == 'folder_id':
                            # フォルダ ID で指定
                            file_id = find_file_id_by_name('派遣業務管理台帳_統合.xlsx', price_parsed['folder_id'])
                            if not file_id:
                                raise Exception('ファイルが見つかりません')
                        else:
                            # gdrive://folder/file 形式
                            folder_id = find_folder_id_by_name(price_parsed['folder_name'])
                            file_id = find_file_id_by_name(price_parsed['file_name'], folder_id)
                            if not file_id:
                                raise Exception('ファイルが見つかりません')

                        # 一時ファイルに保存
                        price_local_path = os.path.join(tempfile.gettempdir(), f'price_{uuid.uuid4()}.xlsx')
                        download_file_from_drive(file_id, price_local_path)
                        app.logger.info(f'金額リストをダウンロード: {price_local_path}')

                    except Exception as drive_error:
                        app.logger.error(f'Google Drive アクセスエラー: {drive_error}')
                        return jsonify({
                            'success': False,
                            'message': f'エラー：Google Drive ファイルにアクセスできません\n{str(drive_error)}'
                        }), 400
                else:
                    # ローカルパスの場合
                    app.logger.info('金額リストはローカルパス')
                    price_path = Path(price_list)
                    if not price_path.exists():
                        return jsonify({
                            'success': False,
                            'message': f'エラー：金額リストファイルが見つかりません\n{price_list}'
                        }), 400
                    price_local_path = str(price_path)

            except Exception as e:
                app.logger.error(f'金額リスト取得エラー: {e}')
                return jsonify({
                    'success': False,
                    'message': f'エラー：金額リストの取得に失敗しました\n{str(e)}'
                }), 400

            # バリデーション
            if not rows:
                return jsonify({
                    'success': False,
                    'message': 'エラー：見積データが入力されていません'
                }), 400

            # 各行のテキストをトリム
            cleaned_rows = []
            for row in rows:
                cleaned_row = {
                    'company': str(row.get('company', '')).strip(),
                    'project': str(row.get('project', '')).strip(),
                    'person': str(row.get('person', '')).strip(),
                    'deadline': str(row.get('deadline', '')).strip(),
                    'period': str(row.get('period', '')).strip(),
                    'workload': str(row.get('workload', '')).strip()
                }
                cleaned_rows.append(cleaned_row)

            app.logger.info(f'見積内容を処理中...')
            app.logger.info(f'見積件数: {len(cleaned_rows)}')

            # Excelファイルに書き込む（取得したローカルパスを使用）
            estimate_results = []
            write_success = False
            write_message = ''

            if mgmt_local_path and price_local_path:
                try:
                    estimate_results = write_to_excel(mgmt_local_path, cleaned_rows, price_local_path)
                    write_success = True
                    write_message = f'✅ ファイルのシート「見積書」に{len(estimate_results)}件の見積データを書き込みました'
                    app.logger.info(write_message)

                    # マクロ情報を確認
                    macro_result = check_excel_macros(mgmt_local_path)
                    if macro_result['has_macros']:
                        write_message += f'\n\n📊 マクロ情報:\n{macro_result["macro_info"]}'
                        app.logger.info(f'マクロ確認: {macro_result["macro_info"]}')

                except Exception as write_error:
                    app.logger.error(f'Excel書き込みエラー: {write_error}')
                    write_message = f'⚠️ ファイル書き込みエラー: {str(write_error)}'

            # セッション ID を生成
            session_id = str(uuid.uuid4())

            # データをメモリに保存
            estimate_data[session_id] = {
                'rows': cleaned_rows,
                'management_file': mgmt_local_path,
                'price_list': price_local_path,
                'management_file_original': management_file,
                'price_list_original': price_list,
                'created_at': datetime.now().isoformat()
            }

            for i, row in enumerate(cleaned_rows, 1):
                app.logger.info(f"  {i}. {row.get('company')} - {row.get('project')}")

            # メッセージを構築
            success_message = f'見積内容が保存されました（{len(cleaned_rows)}件）'
            if write_message:
                success_message += f'\n\n{write_message}'

            return jsonify({
                'success': True,
                'message': success_message,
                'session_id': session_id,
                'data': estimate_results,
                'write_success': write_success
            })

        except Exception as error:
            app.logger.error(f'エラー: {error}')
            return jsonify({
                'success': False,
                'message': '見積内容の保存に失敗しました',
                'error': str(error)
            }), 500


    @app.route('/api/generate-estimate', methods=['POST'])
    def generate_estimate():
        """
        ステップ④：見積書を生成してフォルダに保存
        """
        try:
            try:
                data = request.get_json()
            except Exception as json_error:
                # JSON デコードに失敗した場合、リクエストボディを手動でパース
                app.logger.warning(f'JSON デコード失敗: {json_error}. リクエストボディを手動パース')
                raw_data = request.get_data(as_text=True)
                data = json.loads(raw_data)

            session_id = data.get('session_id')
            output_folder = data.get('output_folder')
            management_file = data.get('management_file')

            # デバッグ出力
            app.logger.info(f'[DEBUG] session_id: {session_id}')
            app.logger.info(f'[DEBUG] output_folder: {output_folder}')
            app.logger.info(f'[DEBUG] management_file: {management_file}')

            # 出力フォルダの確認
            if not output_folder:
                return jsonify({
                    'success': False,
                    'message': 'エラー：見積書格納フォルダが指定されていません'
                }), 400

            output_path = Path(output_folder)
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
                app.logger.info(f'出力フォルダを作成しました: {output_path}')

            # VBA マクロ「EstimatesGen」の Python 実装版を使用
            # 管理ファイルから生成対象の見積を抽出して、見積No ごとに見積書ファイルを生成
            if management_file:
                app.logger.info(f'見積書生成を開始: {management_file}')
                macro_result = generate_estimate_sheets(management_file, output_folder)

                if macro_result['success']:
                    app.logger.info(f'見積書生成成功: {macro_result["message"]}')
                    return jsonify({
                        'success': True,
                        'message': macro_result['message'],
                        'files': macro_result['files'],
                        'count': len(macro_result['files']),
                        'output_folder': str(output_path)
                    })
                else:
                    app.logger.error(f'見積書生成失敗: {macro_result["message"]}')
                    return jsonify({
                        'success': False,
                        'message': macro_result['message']
                    }), 500

            # management_file がない場合はセッションデータから生成
            # セッションデータを取得
            if session_id not in estimate_data:
                return jsonify({
                    'success': False,
                    'message': 'セッションデータが見つかりません'
                }), 400

            session_info = estimate_data[session_id]
            rows = session_info['rows']

            # 以下は従来のファイル生成ロジック（保留中）
            # 見積書ファイルを生成
            generated_files = []
            today = datetime.now().strftime('%Y%m%d')
            estimate_no_prefix = datetime.now().strftime('NS%y%m')
            estimate_counter = 1

            for i, row in enumerate(rows, 1):
                try:
                    # ファイル名用に清掃（スペースのみを削除）
                    company = row.get('company', '会社').strip()
                    project = row.get('project', '案件').strip()
                    deadline = row.get('deadline', today).strip()

                    # スペース（全角・半角）のみを削除（日本語や括弧は保持）
                    company_clean = company.replace(' ', '').replace('　', '')
                    project_clean = project.replace(' ', '').replace('　', '')

                    # 見積期限：最初の日付部分を抽出（例：「2026/11/1 ～ 2027/3/31」→「20261101」）
                    deadline_clean = deadline.replace(' ', '').replace('　', '')
                    # スラッシュを削除して日付のみ抽出
                    deadline_clean = deadline_clean.replace('/', '')
                    # 波線以降は不要（最初の日付のみを使用）
                    if '～' in deadline_clean:
                        deadline_clean = deadline_clean.split('～')[0].strip()
                    elif '~' in deadline_clean:
                        deadline_clean = deadline_clean.split('~')[0].strip()

                    # ファイル名を生成（スペースなし）
                    estimate_no = f'{estimate_no_prefix}{str(estimate_counter).zfill(2)}'
                    filename = f"{company_clean}_{project_clean}_{deadline_clean}_{estimate_no}.xlsx"
                    file_path = output_path / filename

                    app.logger.info(f'見積書ファイルを生成: {file_path}')

                    # 見積書テンプレートから新しいファイルを作成
                    if management_file and Path(management_file).exists():
                        try:
                            from openpyxl import load_workbook
                            import shutil

                            # テンプレートを開いてコピー
                            template_wb = load_workbook(management_file)
                            template_wb.save(str(file_path))
                            template_wb.close()
                            app.logger.info(f'見積書ファイルを作成: {filename}')
                        except Exception as copy_error:
                            app.logger.warning(f'テンプレートコピーエラー: {copy_error}、簡易版で作成します')
                            # コピー失敗時は簡易版を作成
                            from openpyxl import Workbook
                            wb = Workbook()
                            ws = wb.active
                            ws['A1'] = '見積書'
                            ws['A2'] = f"案件名: {project}"
                            ws['A3'] = f"会社: {company}"
                            ws['A4'] = f"見積No: {estimate_no}"
                            wb.save(str(file_path))
                            wb.close()
                    else:
                        # テンプレートがない場合は、空のExcelファイルを作成
                        from openpyxl import Workbook
                        wb = Workbook()
                        ws = wb.active
                        ws['A1'] = '見積書'
                        ws['A2'] = f"案件名: {project}"
                        ws['A3'] = f"会社: {company}"
                        ws['A4'] = f"見積No: {estimate_no}"
                        wb.save(str(file_path))
                        wb.close()
                        app.logger.info(f'見積書ファイルを作成（簡易版）: {filename}')

                    # ファイル存在確認
                    if file_path.exists():
                        app.logger.info(f'✅ ファイル生成確認: {file_path}')
                        generated_files.append(filename)
                    else:
                        app.logger.error(f'❌ ファイル生成失敗: {file_path}')

                    estimate_counter += 1

                except Exception as e:
                    app.logger.error(f'見積書ファイル生成エラー（行{i}）: {type(e).__name__}: {str(e)}')
                    import traceback
                    app.logger.error(traceback.format_exc())
                    continue

            if not generated_files:
                return jsonify({
                    'success': False,
                    'message': '見積書の生成に失敗しました'
                }), 500

            app.logger.info(f'見積書を生成しました（{len(generated_files)}件）')
            for filename in generated_files:
                app.logger.info(f"  - {filename}")

            return jsonify({
                'success': True,
                'message': f'見積書が生成されました（{len(generated_files)}件）',
                'files': generated_files,
                'count': len(generated_files),
                'output_folder': str(output_path)
            })

        except Exception as error:
            app.logger.error(f'見積書生成エラー: {error}')
            return jsonify({
                'success': False,
                'message': f'見積書の生成に失敗しました：{str(error)}',
                'error': str(error)
            }), 500


    @app.route('/api/generate-pdf', methods=['POST'])
    def generate_pdf():
        """
        ステップ⑤：正式版見積書を作成
        ステップ④で生成したExcelファイルをPDFに変換して保存
        ファイル名は Excelと同じ名前（.xlsx → .pdf）
        """
        try:
            data = request.get_json()
            output_folder = data.get('output_folder')
            excel_files_param = data.get('excel_files', [])  # ステップ④で生成したファイル一覧

            if not output_folder:
                return jsonify({
                    'success': False,
                    'message': 'エラー：出力フォルダが指定されていません'
                }), 400

            output_path = Path(output_folder)
            if not output_path.exists():
                return jsonify({
                    'success': False,
                    'message': f'エラー：フォルダが見つかりません：{output_folder}'
                }), 400

            # PDF 生成処理
            result = generate_pdf_from_excel(excel_files_param, output_folder)

            if result['success']:
                return jsonify({
                    'success': True,
                    'message': result['message'],
                    'files': result['files'],
                    'count': len(result['files']),
                    'failed_count': len(result['failed']),
                    'output_folder': str(output_path)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': result['message']
                }), 500

        except Exception as error:
            app.logger.error(f'PDF生成エラー: {error}')
            import traceback
            app.logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'message': f'PDF生成エラー：{str(error)}'
            }), 500
