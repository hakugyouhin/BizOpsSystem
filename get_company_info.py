# -*- coding: utf-8 -*-
"""
VBA の cmyInfoGet() 関数を Python で実装
会社一覧シートから会社情報を取得
"""

from openpyxl import load_workbook
import logging

app_logger = logging.getLogger(__name__)

def get_company_info(management_file, company_name):
    """
    会社一覧シートから会社情報を取得

    VBA の cmyInfoGet() 相当の実装

    Args:
        management_file (str): 管理ファイルパス
        company_name (str): 会社名（略称）（検索キー）

    Returns:
        dict: {
            'postal_code': '〒123-4567',
            'address1': '東京都渋谷区',
            'address2': '1-2-3',
            'company_name': '株式会社〇〇',
            'president_name': '田中太郎'
        } または None（見つからない場合）
    """

    company_info = {
        'postal_code': '',
        'address1': '',
        'address2': '',
        'company_name': '',
        'president_name': ''
    }

    try:
        # 管理ファイルを開く
        wb = load_workbook(management_file, data_only=True)

        if '会社一覧' not in wb.sheetnames:
            app_logger.error('「会社一覧」シートが見つかりません')
            wb.close()
            return None

        ws = wb['会社一覧']

        # ヘッダー行は Row 3
        header_row = 3

        # Row 4 から検索開始（VBA: For i = 4 To 1000）
        for row_idx in range(4, 1001):
            # Column C (3) = 会社名（略称）= 検索キー
            cell_value = ws.cell(row_idx, 3).value

            # 空行までで検索終了（VBA: If ... = "" Then Exit For）
            if cell_value is None or cell_value == '':
                break

            # 会社名が一致したら情報を取得
            if company_name == cell_value:
                # Column D (4) = 会社名（正式）
                company_info['company_name'] = ws.cell(row_idx, 4).value or ''

                # Column E (5) = 郵便番号
                company_info['postal_code'] = ws.cell(row_idx, 5).value or ''

                # Column F (6) = 住所（改行で複数行）
                address_full = ws.cell(row_idx, 6).value or ''

                # VBA: pos = InStr(cmpListSht.Cells(i, 6).Value, vbLf)
                # Python: split('\n') で分割
                if '\n' in address_full:
                    addresses = address_full.split('\n')
                    company_info['address1'] = addresses[0] if len(addresses) > 0 else ''
                    company_info['address2'] = addresses[1] if len(addresses) > 1 else ''
                else:
                    # 改行がない場合は住所1のみ
                    company_info['address1'] = address_full
                    company_info['address2'] = ''

                # Column I (9) = 代表取締役
                company_info['president_name'] = ws.cell(row_idx, 9).value or ''

                app_logger.info(f'会社情報取得成功: {company_name} → {company_info["company_name"]}')
                wb.close()
                return company_info

        # 見つからない場合
        app_logger.warning(f'会社名が見つかりません: {company_name}')
        wb.close()
        return None

    except Exception as e:
        app_logger.error(f'会社情報取得エラー: {e}')
        import traceback
        app_logger.error(traceback.format_exc())
        return None


# テスト
if __name__ == '__main__':
    import sys

    logging.basicConfig(level=logging.INFO)

    management_file = r"G:\マイドライブ\96_tmp\20261010\請求書＆注文書生成_双日用_Excel版2.xlsx"

    # テストケース
    test_companies = [
        'オネストインフォ',      # Row 4
        '日新サービス',          # Row 5
        'スマートビラ',          # Row 6
        '存在しない会社'         # Not found
    ]

    print("=" * 100)
    print("会社情報取得関数テスト")
    print("=" * 100)

    for company_name in test_companies:
        print(f"\n【検索: {company_name}】")
        info = get_company_info(management_file, company_name)

        if info:
            print(f"  郵便番号: {info['postal_code']}")
            print(f"  住所1: {info['address1']}")
            print(f"  住所2: {info['address2']}")
            print(f"  会社名: {info['company_name']}")
            print(f"  社長名: {info['president_name']}")
        else:
            print(f"  ❌ 見つかりませんでした")
