# -*- coding: utf-8 -*-
"""
見積書作成システム - Excel操作ユーティリティ
Excel ファイルの読み込み、書き込み、マクロ解析機能を提供
"""

import os
import zipfile
import re
import shutil
import json
from datetime import datetime
from pathlib import Path
from copy import copy as copy_style

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border, Alignment, numbers
from openpyxl.utils import get_column_letter

# グローバルなアプリケーション参照（外部から渡される）
app = None
DATA_DIR = None


def set_app_context(flask_app, data_dir):
    """
    Flask アプリケーションコンテキストを設定

    Args:
        flask_app: Flask アプリケーションインスタンス
        data_dir: データディレクトリパス
    """
    global app, DATA_DIR
    app = flask_app
    DATA_DIR = data_dir


# ========================================
# ZIP レベルでのシートコピー関数（描画オブジェクト保持）
# ========================================

def create_estimate_from_template_zip(template_file, output_file, keep_sheet_index=8):
    """
    テンプレートシートを描画オブジェクト含めてコピー
    ZIP レベルでの操作でシートのすべての要素を保持
    """
    # テンプレートをコピー
    shutil.copy2(template_file, output_file)

    # ZIP ファイルとして処理
    with zipfile.ZipFile(output_file, 'r') as template_zip:
        all_files = {}
        for item in template_zip.infolist():
            all_files[item.filename] = template_zip.read(item)

    # workbook.xml を処理
    wb_xml_str = all_files['xl/workbook.xml'].decode('utf-8')

    # シート定義を抽出
    sheet_pattern = r'<sheet[^>]*name="([^"]*)"[^>]*r:id="(rId\d+)"[^>]*/>'
    sheets = list(re.finditer(sheet_pattern, wb_xml_str))

    # keep_sheet_index 以外を削除
    if len(sheets) > keep_sheet_index:
        rids_to_delete = set()
        for idx, match in enumerate(sheets):
            if idx != keep_sheet_index:
                sheet_tag = match.group(0)
                rid = match.group(2)
                rids_to_delete.add(rid)
                wb_xml_str = wb_xml_str.replace(sheet_tag, '')

        # definedNames を処理
        defined_names_pattern = r'<definedNames>.*?</definedNames>'
        defined_names_match = re.search(defined_names_pattern, wb_xml_str, re.DOTALL)

        if defined_names_match:
            defined_names_str = defined_names_match.group(0)
            defined_name_pattern = r'<definedName[^>]*>([^<]*)</definedName>'

            for match in re.finditer(defined_name_pattern, defined_names_str):
                content = match.group(1)
                remove = False
                for idx in range(len(sheets)):
                    if idx != keep_sheet_index:
                        sheet_name = sheets[idx].group(1)
                        if sheet_name in content:
                            remove = True
                            break

                if remove:
                    defined_name_tag = match.group(0)
                    wb_xml_str = wb_xml_str.replace(defined_name_tag, '')

        wb_xml_str = re.sub(r'\n\s*\n', '\n', wb_xml_str)
        all_files['xl/workbook.xml'] = wb_xml_str.encode('utf-8')

    # workbook.xml.rels を処理
    rels_str = all_files['xl/_rels/workbook.xml.rels'].decode('utf-8')

    for rid in rids_to_delete:
        rel_pattern = r'<Relationship[^>]*Id="' + re.escape(rid) + r'"[^>]*/>'
        match = re.search(rel_pattern, rels_str)
        if match:
            rel_tag = match.group(0)
            rels_str = rels_str.replace(rel_tag, '')

    rels_str = re.sub(r'\n\s*\n', '\n', rels_str)
    all_files['xl/_rels/workbook.xml.rels'] = rels_str.encode('utf-8')

    # 新しい ZIP ファイルを作成
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as out_zip:
        for filename, content in all_files.items():
            if filename == 'xl/calcChain.xml':
                continue
            out_zip.writestr(filename, content)

    return output_file


# ========================================
# マクロ解析機能
# ========================================

def check_excel_macros(excel_file):
    """
    Excelファイル（.xlsm）にマクロが含まれているか確認

    Args:
        excel_file: Excelファイルパス

    Returns:
        {'has_macros': bool, 'macro_info': str}
    """
    try:
        excel_path = Path(excel_file)
        if not excel_path.exists():
            return {'has_macros': False, 'macro_info': 'ファイルが見つかりません'}

        if not excel_path.suffix.lower() == '.xlsm':
            return {'has_macros': False, 'macro_info': '.xlsmファイルではありません'}

        # .xlsm は ZIP ファイル形式なので、VBA プロジェクトを確認
        try:
            with zipfile.ZipFile(excel_file, 'r') as zip_ref:
                # VBA プロジェクトが含まれているか確認
                file_list = zip_ref.namelist()
                has_vba = any('xl/vbaProject' in f for f in file_list)

                if has_vba:
                    # マクロが含まれている場合、シート情報も取得
                    macro_info = '✅ マクロが含まれています'
                    # ワークシート名を取得
                    try:
                        wb = load_workbook(excel_file)
                        sheets = wb.sheetnames
                        macro_info += f'\nシート一覧: {", ".join(sheets)}'
                        wb.close()
                    except:
                        pass
                    return {'has_macros': True, 'macro_info': macro_info}
                else:
                    return {'has_macros': False, 'macro_info': 'マクロは含まれていません'}
        except Exception as zip_error:
            return {'has_macros': False, 'macro_info': f'解析エラー: {str(zip_error)}'}

    except Exception as error:
        return {'has_macros': False, 'macro_info': f'エラー: {str(error)}'}


# ========================================
# ヘルパー関数
# ========================================

def get_unit_price_from_ledger(price_list_file, person_name):
    """
    金額リストファイルから担当者の単価を取得

    Args:
        price_list_file: 金額リストファイル名
        person_name: 担当者名

    Returns:
        {'success': True, 'price': 単価} または {'success': False, 'error': エラーメッセージ}
    """
    try:
        if not price_list_file:
            return {'success': False, 'error': '金額リストファイルが指定されていません'}

        # ファイルパスを解析
        if price_list_file.startswith('/') or (len(price_list_file) > 1 and price_list_file[1] == ':'):
            price_file = Path(price_list_file)
        else:
            price_file = DATA_DIR / price_list_file

        if not price_file.exists():
            return {'success': False, 'error': f'金額リストファイルが見つかりません: {price_file}'}

        wb = load_workbook(price_file, data_only=True)

        # 「案件・契約台帳」シートを探す
        sheet_name = '案件・契約台帳'
        if sheet_name not in wb.sheetnames:
            return {'success': False, 'error': f'シート「{sheet_name}」が見つかりません'}

        ws = wb[sheet_name]

        # ヘッダー行から列インデックスを取得（Row 4 がヘッダー）
        header_row = 4
        person_col = 5   # デフォルト: E列
        price_col = 8    # デフォルト: H列

        # ヘッダーを探す
        for col_idx in range(1, min(ws.max_column + 1, 20)):
            header_val = ws.cell(header_row, col_idx).value
            if header_val:
                header_str = str(header_val).strip()
                if '担当' in header_str or 'スタッフ' in header_str:
                    person_col = col_idx
                # 派遣単価（H列）を優先、コスト単価（I列）は使用しない
                if '派遣' in header_str and '単価' in header_str:
                    price_col = col_idx

        if app:
            app.logger.info(f'金額リスト: 担当者列={person_col}, 単価列={price_col}')

        # 検索用に人名のスペースを削除
        person_name_normalized = person_name.strip().replace(' ', '').replace('　', '')
        if app:
            app.logger.info(f'検索キーワード: {person_name} → {person_name_normalized}')

        # データ行を検索（Row 5 以降）
        for row_idx in range(5, ws.max_row + 1):
            person_cell = ws.cell(row_idx, person_col).value
            if person_cell:
                # 金額リストの名前もスペース削除して比較
                list_person_normalized = str(person_cell).strip().replace(' ', '').replace('　', '')
                if list_person_normalized == person_name_normalized:
                    price_cell = ws.cell(row_idx, price_col).value
                    try:
                        price_val = float(price_cell) if price_cell else 0
                        if price_val <= 0:
                            if app:
                                app.logger.warning(f'単価が0またはマイナスです: {person_name} = {price_val}')
                            return {'success': False, 'error': f'担当者「{person_name}」の単価が正しく設定されていません'}
                        if app:
                            app.logger.info(f'単価を取得: {person_name} = {price_val}')
                        return {'success': True, 'price': price_val}
                    except (ValueError, TypeError):
                        if app:
                            app.logger.warning(f'単価が数値ではありません: {price_cell}')
                        return {'success': False, 'error': f'担当者「{person_name}」の単価が数値ではありません'}

        # 見つからない場合
        error_msg = f'エラー：金額リストに担当者「{person_name}」が見つかりません。\n金額リストを確認してください。'
        if app:
            app.logger.warning(error_msg)
        return {'success': False, 'error': error_msg}

    except Exception as error:
        if app:
            app.logger.error(f'金額リスト取得エラー: {error}')
        return {'success': False, 'error': f'金額リスト検索エラー: {str(error)}'}


def generate_unique_estimate_no(ws, col_idx, estimate_date):
    """
    見積No を生成（N + YYMM + 採番、重複チェック付き）

    Args:
        ws: Worksheet オブジェクト
        col_idx: 見積No が格納される列番号（P列 = 16）
        estimate_date: 見積日（datetime）

    Returns:
        unique_estimate_no: 重複のない見積No（例: N2610001）
    """
    if not col_idx:
        # 見積No列が見つからない場合は、デフォルト形式で返す
        return 'N' + estimate_date.strftime('%y%m') + '0001'

    # 見積No のプレフィックス生成
    estimate_no_prefix = 'N' + estimate_date.strftime('%y%m')  # N + YYMM

    # P列（見積No列）全体をスキャンして、既存の番号を取得
    existing_numbers = set()
    for row_idx in range(5, ws.max_row + 1):
        cell_value = ws.cell(row_idx, col_idx).value
        if cell_value and isinstance(cell_value, str):
            existing_numbers.add(cell_value)

    # 採番を決定
    counter = 1
    while True:
        candidate_no = f'{estimate_no_prefix}{str(counter).zfill(3)}'
        # 例: N2610 + 001 = N2610001

        if candidate_no not in existing_numbers:
            return candidate_no

        counter += 1


def write_to_excel(management_file, rows, price_list_file):
    """
    見積データをExcelファイル（見積書シート）に書き込む

    Args:
        management_file: 管理Excelファイルのパス
        rows: 見積データの行リスト
        price_list_file: 金額リストファイル名
    """
    try:
        # ファイルパスを解析
        if management_file.startswith('/') or (len(management_file) > 1 and management_file[1] == ':'):
            excel_file = Path(management_file)
        else:
            excel_file = DATA_DIR / management_file

        if not excel_file.exists():
            if app:
                app.logger.warning(f'Excelファイルが見つかりません: {excel_file}')
            raise FileNotFoundError(f'File not found: {excel_file}')

        if app:
            app.logger.info(f'Excelファイルを開きます: {excel_file}')

        # .xlsm ファイルの場合、マクロを保持できないため、データのみを読み込む
        # 注：openpyxl は .xlsm ファイルのマクロを保存できないため、
        # ユーザーが手動でマクロを実行する必要があります
        wb = load_workbook(excel_file, data_only=False)

        # 「見積書」シートを探す
        sheet_name = '見積書'
        if sheet_name not in wb.sheetnames:
            raise ValueError(f'Sheet "{sheet_name}" not found')

        ws = wb[sheet_name]
        if app:
            app.logger.info(f'シートを開きました: {sheet_name}')

        # ヘッダー行を取得（Row 4）
        header_row = 4
        col_map = {}

        # ヘッダーからカラムを取得
        for col_idx in range(1, ws.max_column + 1):
            header = str(ws.cell(header_row, col_idx).value or '').strip()
            if header:
                col_map[header] = col_idx

        if app:
            app.logger.info(f'カラムマッピング（全詳細）:')
            for key, idx in sorted(col_map.items()):
                col_letter = get_column_letter(idx)
                app.logger.info(f'  {col_letter}列: {key}')

        # 既存データの「生成対象」欄をクリア
        generate_col = col_map.get('生成対象')
        if generate_col:
            for row_idx in range(header_row + 1, ws.max_row + 1):
                if ws.cell(row_idx, generate_col).value == '●':
                    ws.cell(row_idx, generate_col).value = None

        # 新しいレコードを追加する位置を決定（最後のデータ行 + 1）
        next_row = header_row + 1
        for row_idx in range(header_row + 1, ws.max_row + 1):
            # A列、B列、C列のいずれかに値があるなら、その行はデータ行
            if (ws.cell(row_idx, 1).value or  # A列
                ws.cell(row_idx, 2).value or  # B列（会社名）
                ws.cell(row_idx, 3).value):   # C列（支払条件）
                next_row = row_idx + 1

        today = datetime.now()

        # 複数担当者を分割して複数レコードを生成
        expanded_rows = []
        for row_data in rows:
            person = row_data.get('person', '').strip()

            # 担当者が「、」で複数指定されている場合、分割
            if '、' in person:
                # 複数担当者を分割
                persons = [p.strip() for p in person.split('、') if p.strip()]
                # 各担当者ごとに新しいレコードを生成
                for single_person in persons:
                    new_row = row_data.copy()
                    new_row['person'] = single_person
                    expanded_rows.append(new_row)
                if app:
                    app.logger.info(f'複数担当者を分割: {person} → {persons}')
            else:
                expanded_rows.append(row_data)

        if app:
            app.logger.info(f'展開後の見積件数: {len(expanded_rows)} （元の件数: {len(rows)}）')
        rows = expanded_rows  # 展開されたrows を使用

        # 見積No を生成（複数レコード処理時は、すべて同じ見積No を使用）
        # P列のヘッダーが '見積No' または '見積No:' の可能性がある
        estimate_no_col = col_map.get('見積No') or col_map.get('見積No:')
        if not estimate_no_col:
            # デバッグ：すべてのキーを出力
            if app:
                app.logger.warning(f'見積No列が見つかりません。col_map: {list(col_map.keys())}')
        estimate_no = generate_unique_estimate_no(ws, estimate_no_col, today)

        # 見積データを書き込み
        estimate_results = []
        for idx, row_data in enumerate(rows, 1):
            # マッピング
            company = '双日'
            project = row_data.get('project', '').strip()
            person = row_data.get('person', '').strip()
            deadline = row_data.get('deadline', '').strip()
            period_str = row_data.get('period', '').strip()

            # プロジェクト名から日付部分を削除（括弧内の日付情報）
            project = re.sub(r'（[^）]*年[^）]*）', '', project).strip()

            # 担当者がある場合、プロジェクト名に付与
            if person:
                project = f"{project}（作業者：{person}）"

            # 単価を取得（スペース削除後に検索）
            price_result = get_unit_price_from_ledger(price_list_file, person)

            if not price_result['success']:
                # 見つからない場合はエラーを記録して処理を中止
                error_msg = price_result['error']
                if app:
                    app.logger.error(f'行{idx}のエラー: {error_msg}')
                raise ValueError(error_msg)

            unit_price = price_result['price']

            # 金額を計算
            try:
                quantity = float(period_str) if period_str else 0
            except (ValueError, TypeError):
                quantity = 0

            # 前の行が存在する場合、B列のNo をインクリメント
            if next_row > header_row + 1:
                prev_no_cell = ws.cell(next_row - 1, 2)  # B列（No）
                if prev_no_cell.value:
                    try:
                        no_value = int(prev_no_cell.value) + 1
                    except (ValueError, TypeError):
                        no_value = 1
                else:
                    no_value = 1
            else:
                no_value = 1

            # セルに書き込み
            write_data = {
                'No': no_value,                              # B列（新規：No をインクリメント）
                '生成対象': '●',
                '会社名': company,
                '支払条件': '月末締翌月末払',
                '作業期限': deadline,
                '見積書No': idx,
                'プロジェクト名': project,
                'ユーザー名': '-',
                '数量': quantity,
                '単位': '人月',                               # J列（単位に「人月」）
                '単価': unit_price,                          # K列（単価）
                '金額': f'=J{next_row}*L{next_row}',        # M列（数式：J×L）
                '摘要': None,                                # N列（クリア）
                '見積日': today,                             # 日付型で書き込み
                '見積No': estimate_no,                       # P列（新形式）
                '見積No:': estimate_no                       # P列（'見積No:' キーの可能性対応）
            }

            # 上行が存在する場合、書式をコピー
            if next_row > header_row + 1:
                for col_idx in range(1, ws.max_column + 1):
                    source_cell = ws.cell(next_row - 1, col_idx)
                    target_cell = ws.cell(next_row, col_idx)

                    # セルのスタイルをコピー
                    if source_cell.has_style:
                        target_cell.font = copy_style(source_cell.font)
                        target_cell.border = copy_style(source_cell.border)
                        target_cell.fill = copy_style(source_cell.fill)
                        target_cell.number_format = copy_style(source_cell.number_format)
                        target_cell.protection = copy_style(source_cell.protection)
                        target_cell.alignment = copy_style(source_cell.alignment)

            # セルに書き込み（数式と値を区別）
            for col_name, col_value in write_data.items():
                col_idx = col_map.get(col_name)
                if col_idx:
                    cell = ws.cell(row=next_row, column=col_idx)

                    if isinstance(col_value, str) and col_value.startswith('='):
                        # 数式の場合
                        cell.value = col_value
                    elif col_name == '見積日' and isinstance(col_value, datetime):
                        # 見積日：日付型で書き込み、YYYY/MM/DD 形式を設定
                        cell.value = col_value
                        cell.number_format = 'yyyy/mm/dd'
                    else:
                        # その他の値
                        cell.value = col_value

            # N列（摘要）をクリア（明示的に空白にする）
            摘要_col = col_map.get('摘要')
            if 摘要_col:
                ws.cell(row=next_row, column=摘要_col).value = None

            # 金額の計算値（数式の結果）をレスポンスに含める
            amount = quantity * unit_price

            estimate_results.append({
                'company': company,
                'project': project,
                'person': person,
                'deadline': deadline,
                'period': quantity,
                'unit_price': unit_price,
                'amount': amount,
                'estimate_no': estimate_no
            })

            if app:
                app.logger.info(f'行 {next_row} に見積データを書き込み: {project} (見積No: {estimate_no}, 金額: {amount})')

            next_row += 1

        # ファイルを保存してクローズ
        try:
            wb.save(excel_file)
            if app:
                app.logger.info(f'Excelファイルを保存しました: {excel_file}')
            if str(excel_file).endswith('.xlsm'):
                if app:
                    app.logger.warning(f'.xlsm ファイルはopenpyxlでマクロを保持できません。マクロ実行はExcelで手動実行してください。')
        except Exception as save_error:
            if app:
                app.logger.error(f'ファイル保存エラー: {save_error}')
            raise
        finally:
            wb.close()

        return estimate_results

    except Exception as error:
        if app:
            app.logger.error(f'Excel書き込みエラー: {error}')
        try:
            wb.close()
        except:
            pass
        raise


def generate_estimate_sheets(management_file, output_folder):
    """
    見積書シートから生成対象（●）の行を読み込んで、
    見積書テンプレートファイルに記入し、見積No ごとに個別ファイルを生成

    Args:
        management_file: 管理Excelファイルパス
        output_folder: 出力先フォルダ

    Returns:
        {'success': bool, 'files': [ファイルパス], 'message': str}
    """
    try:
        management_path = Path(management_file)
        output_path = Path(output_folder)
        template_path = Path(__file__).parent.parent / 'OfficeTemplate' / '見積書テンプレート.xlsx'

        if not management_path.exists():
            return {'success': False, 'message': f'管理ファイルが見つかりません: {management_path}'}

        # テンプレートファイルが存在しない場合は、管理ファイルをテンプレートとして使用
        if not template_path.exists():
            if app:
                app.logger.info(f'テンプレートファイルが見つかりません。管理ファイルをテンプレートとして使用します')
            template_path = management_path

        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        if app:
            app.logger.info(f'見積書生成処理を開始します')

        # 管理ファイルを開く
        try:
            wb_mgmt = load_workbook(management_file)
        except Exception as e:
            if app:
                app.logger.error(f'Excel ファイルを開く際のエラー: {e}')
                app.logger.error(f'ファイルパス: {management_file}')
                app.logger.error(f'ファイルサイズ: {Path(management_file).stat().st_size} bytes')
            raise Exception(f"Excel ファイルを開けません: {str(e)}")

        if '見積書' not in wb_mgmt.sheetnames:
            return {'success': False, 'message': 'シート「見積書」が見つかりません'}

        ws_list = wb_mgmt['見積書']

        # ヘッダー行を取得（Row 4）
        header_row = 4
        col_map = {}

        # カラムマッピングを取得
        for col_idx in range(1, ws_list.max_column + 1):
            header = str(ws_list.cell(header_row, col_idx).value or '').strip()
            if header:
                col_map[header] = col_idx

        if app:
            app.logger.info(f'カラムマッピング: {list(col_map.keys())}')

        # 生成対象（●）の行を抽出
        generate_col = col_map.get('生成対象')
        if not generate_col:
            return {'success': False, 'message': '「生成対象」カラムが見つかりません'}

        # 見積書データを抽出（見積No ごとにグループ化）
        estimate_groups = {}  # {見積No: [データ行1, データ行2, ...]}

        for row_idx in range(header_row + 1, ws_list.max_row + 1):
            if ws_list.cell(row_idx, generate_col).value == '●':
                # この行のデータを抽出
                row_data = {}
                for col_name, col_idx in col_map.items():
                    row_data[col_name] = ws_list.cell(row_idx, col_idx).value

                # 見積No を取得（複数のキー名に対応）
                estimate_no = row_data.get('見積No:', '') or row_data.get('見積No', '') or row_data.get('見積書No', '')
                if estimate_no:
                    if estimate_no not in estimate_groups:
                        estimate_groups[estimate_no] = []
                    estimate_groups[estimate_no].append(row_data)

        if app:
            app.logger.info(f'生成対象の見積No数: {len(estimate_groups)}')

        if not estimate_groups:
            return {'success': False, 'message': '生成対象の見積（●）が見つかりません'}

        # 見積No ごとに見積書ファイルを生成
        generated_files = []
        for estimate_no, data_rows in estimate_groups.items():
            wb_estimate = None
            temp_estimate_file = None
            try:
                first_data = data_rows[0]
                if app:
                    app.logger.info(f'見積書を生成中: {estimate_no} - {len(data_rows)}件のデータ')

                # ファイル名を生成（最初に生成して、テンポラリパスに使用）
                project_name = first_data.get('プロジェクト名', '案件')
                deadline = first_data.get('作業期限', '')
                # スペース（全角・半角）を削除
                deadline = deadline.replace('　', '').replace(' ', '')
                if app:
                    app.logger.info(f'[DEBUG] deadline (スペース削除後): {repr(deadline)}')
                project_name_clean = re.sub(r'（作業者：[^）]*）', '', project_name)

                def format_date_to_yyyymmdd(date_str):
                    """YYYY/M/D → YYYYMMDD に変換（0パディング対応）"""
                    match = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str.strip())
                    if match:
                        year, month, day = match.groups()
                        return f'{year}{month.zfill(2)}{day.zfill(2)}'
                    return date_str

                if '～' in deadline:
                    start_date, end_date = deadline.split('～')
                    deadline_for_filename = f'{format_date_to_yyyymmdd(start_date)}～{format_date_to_yyyymmdd(end_date)}'
                else:
                    deadline_for_filename = format_date_to_yyyymmdd(deadline)

                output_filename = f'見積書_{project_name_clean}_（{deadline_for_filename}）_{estimate_no}.xlsx'
                output_filename = output_filename.replace('　', '')
                output_file = output_path / output_filename

                # テンプレートファイルを最終出力位置にコピー（画像・オブジェクト保持）
                shutil.copy2(str(template_path), str(output_file))

                # コピーしたファイルの青色ヘッダーの背景色を白に設定
                try:
                    wb_temp = load_workbook(str(output_file))
                    ws_temp = wb_temp.active

                    # 最初の3行全体の背景色をチェックして白に変更
                    white_fill = PatternFill(fill_type='solid', fgColor='FFFFFFFF')

                    for row_idx in range(1, 4):
                        for col_idx in range(1, 20):
                            cell = ws_temp.cell(row_idx, col_idx)
                            # 背景色が設定されている場合、白に変更
                            if cell.fill and cell.fill.fill_type == 'solid' and cell.fill.fgColor:
                                if app:
                                    app.logger.info(f'背景色を変更: 行{row_idx}列{col_idx}')
                                cell.fill = white_fill

                    wb_temp.save(str(output_file))
                    wb_temp.close()
                    if app:
                        app.logger.info(f'青色ヘッダーの背景色を白に変更しました: {output_filename}')
                except Exception as color_error:
                    if app:
                        app.logger.warning(f'背景色変更エラー（スキップ）: {color_error}')

                # コピーしたファイルを開いて値を書き込み
                wb_estimate = load_workbook(str(output_file))
                ws_estimate = wb_estimate.active

                # ===== ヘッダー・固定情報を書き込み =====

                # 見積No（I3）
                estimate_no_val = first_data.get('見積No:', '') or first_data.get('見積No', '') or first_data.get('見積書No', '')
                ws_estimate.cell(3, 9).value = estimate_no_val  # I3

                # 見積日（I4）
                estimate_date = first_data.get('見積日', '')
                ws_estimate.cell(4, 9).value = estimate_date  # I4

                # 支払条件（C11）
                ws_estimate.cell(11, 3).value = first_data.get('支払条件', '')

                # 作業期限（C12）
                ws_estimate.cell(12, 3).value = first_data.get('作業期限', '')

                # データ行を書き込み（複数行対応）B16～, D16～, E16～, F16～, G16～, H16～, I16～
                for idx, data in enumerate(data_rows):
                    data_row = 16 + idx  # Row 16, 17, 18...

                    # プロジェクト名（B列、B16～）
                    ws_estimate.cell(data_row, 2).value = data.get('プロジェクト名', '')

                    # ユーザー名（D列、D16～）
                    ws_estimate.cell(data_row, 4).value = data.get('ユーザー名', '')

                    # 数量（E列、E16～）
                    ws_estimate.cell(data_row, 5).value = data.get('数量', '')

                    # 単位（F列、F16～）
                    ws_estimate.cell(data_row, 6).value = data.get('単位', '')

                    # 単価（G列、G16～）
                    ws_estimate.cell(data_row, 7).value = data.get('単価', '')

                    # 摘要（I列、I16～）
                    ws_estimate.cell(data_row, 9).value = data.get('摘要', '')

                # ファイルに保存
                try:
                    wb_estimate.save(str(output_file))
                    if app:
                        app.logger.info(f'見積書ファイルを保存: {output_file}')
                    generated_files.append({
                        'estimate_no': estimate_no,
                        'filename': output_filename,
                        'filepath': str(output_file)
                    })
                    if app:
                        app.logger.info(f'✅ ファイル生成完了: {output_filename} ({len(data_rows)}件)')

                except Exception as generate_error:
                    if app:
                        app.logger.error(f'見積書生成エラー: {generate_error}')
                    import traceback
                    if app:
                        app.logger.error(traceback.format_exc())
                    continue

                finally:
                    # ワークブックをクローズ（ファイルロック解放）
                    if wb_estimate is not None:
                        try:
                            wb_estimate.close()
                            if app:
                                app.logger.info(f'ワークブックをクローズしました: {output_filename}')
                        except Exception as close_error:
                            if app:
                                app.logger.warning(f'クローズエラー: {close_error}')
                    import gc
                    gc.collect()  # ガベージコレクション実行

            except Exception as e:
                if app:
                    app.logger.error(f'見積書生成エラー（{estimate_no}）: {e}')
                import traceback
                if app:
                    app.logger.error(traceback.format_exc())
            finally:
                # エラーが発生した場合も、ファイルをクローズ
                if wb_estimate is not None:
                    try:
                        wb_estimate.close()
                    except:
                        pass

        try:
            wb_mgmt.close()
        except:
            pass

        if not generated_files:
            return {'success': False, 'message': '見積書の生成に失敗しました'}

        result_files = [f['filename'] for f in generated_files]
        return {
            'success': True,
            'message': f'{len(generated_files)}件の見積書を生成しました',
            'files': result_files,
            'details': generated_files
        }

    except Exception as error:
        if app:
            app.logger.error(f'見積書生成エラー: {error}')
        import traceback
        if app:
            app.logger.error(traceback.format_exc())
        # エラー時も管理ファイルをクローズ
        try:
            wb_mgmt.close()
        except:
            pass
        return {'success': False, 'message': f'エラー: {str(error)}'}
