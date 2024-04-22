import pdfplumber
import sys
import pandas as pd
import numpy as np

from tqdm.auto import tqdm


def get_y_lines(page):
    lines = page.rects
    lines_y = [x for x in lines if (x['width'] < 3) and (x['height'] > 3)]
    vertical_lines = list({(r['x0'] + r['x1']) / 2 for r in lines_y})
    if len(vertical_lines) > 2:
        return vertical_lines

    tbbox = page.find_table().bbox
    table_page = page.crop(tbbox)
    chars_x = sorted([[c['x0'], c['x1']] for c in table_page.chars], key=lambda x: x[0])

    max_x1 = 0
    vertical_lines = [tbbox[0]]
    for i in range(len(chars_x)):
      new_x0, new_x1 = chars_x[i]
      if max_x1 and ((new_x0 - max_x1) > 3): # (new_x1 - new_x0)):
        vertical_lines.append((new_x0 + max_x1 ) / 2)
      if chars_x[i][1] > max_x1:
        max_x1 = chars_x[i][1]
    vertical_lines.append(tbbox[2])
    return vertical_lines


def filter_rects(candidates_rects):
    candidates_rects_filtered = []
    for cr in candidates_rects:
        new_rect = True
        for prev_cr in candidates_rects_filtered:
            if cr['stroking_color'] is None and cr['non_stroking_color'] is None:
                new_rect = False
                break
            elif (cr['stroking_color'] is not None and (cr['stroking_color'] == prev_cr['stroking_color'])) or \
               (cr['non_stroking_color'] is not None and (cr['non_stroking_color'] == prev_cr['non_stroking_color'])):
                if (cr['x0'] >= prev_cr['x0']) and \
                    (cr['y0'] >= prev_cr['y0']) and \
                    (cr['x1'] <= prev_cr['x1']) and \
                    (cr['y1'] <= prev_cr['y1']):
                    new_rect = False
                    break
        if new_rect == True:
            candidates_rects_filtered.append(cr)
    return candidates_rects_filtered


def get_x_lines(page):
    lines = page.rects
    lines_y = [x for x in lines if (x['width'] < 3) and (x['height'] > 3)]
    lines_x = [x for x in lines if (x['height'] < 3) and (x['width'] > 3)]
    max_bottom = max([y['bottom'] for y in lines_y])

    lines_x = [x for x in lines_x if (x['bottom'] <= max_bottom + 3)]
    bottom_line = max(
        [(r['top'] + r['bottom']) / 2 for r in lines_x])
    bottom_rects_x = [
        r for r in lines_x if ((r['top'] + r['bottom']) / 2) == bottom_line]

    tbbox = page.find_table().bbox
    table_page = page.crop(tbbox)
    max_top = min([x['top'] for x in lines_x])
    candidates_x = set()
    candidates_rects = [x for x in table_page.rects if (x['width'] > 10) and (x['height'] > 10)]
    candidates_rects = filter_rects(candidates_rects)
    candidates_rects = filter_rects(candidates_rects[::-1])

    for candidate_rect in candidates_rects:
        for k in ['top', 'bottom']:
            if candidate_rect[k] < max_top - 3:
                candidates_x.add(candidate_rect[k])
    candidates_x = sorted(list(candidates_x))
    for i in range(len(candidates_x) - 1, 0, -1):
        if candidates_x[i] - candidates_x[i-1] < 3:
            candidates_x.pop(i)
    return lines_x + [bottom_line] + list(candidates_x), bottom_rects_x


def update_column(column, new_bbox):
    column[0] = max(column[0], new_bbox[0])
    column[1] = min(column[1], new_bbox[2])


def update_row(row, new_bbox):
    row[0] = max(row[0], new_bbox[1])
    row[1] = min(row[1], new_bbox[3])


def cell_in_cell(small, big):
    left = small[0] >= big[0]
    right = small[2] <= big[2]
    top = small[1] >= big[1]
    bottom = small[3] <= big[3]
    return left and right and top and bottom


def shortest_combination(str1, str2):
    str1 = str1 or ''
    str2 = str2 or ''
    common_length = 0
    min_length = min(len(str1), len(str2))
    for i in range(min_length):
        if str1[len(str1)-i-1:] == str2[:i+1]:
            common_length = i + 1
    return str1 + str2[common_length:]


def get_rows_and_columns(tables, tables_cells):
    columns = []
    rows = []
    last_columns = []
    for k in tqdm(range(len(tables)), desc="Calculate coordinates for rows and columns", leave=False):
        columns.append([])
        rows.append([])
        last_columns.append([])
        for t in tables_cells[k]:
            for i, r in enumerate(t.rows):
                for j, c in enumerate(r.cells):
                    if i >= len(rows[k]):
                        rows[k].append([-1e9, 1e9])
                    if j >= len(columns[k]):
                        columns[k].append([-1e9, 1e9])
                    if j >= len(last_columns[k]):
                        last_columns[k].append(None)
                    if c is not None:
                        update_column(columns[k][j], c)
                        update_row(rows[k][i], c)
                        last_columns[k][j] = i
    return rows, columns, last_columns


def get_columns_to_continue(tables, bottom_rects_x_list, columns, last_columns):
    columns_to_continue = []
    for k in tqdm(range(len(tables)), desc="Find page-separated table cells", leave=False):
        for j, c in enumerate(columns[k]):
            limited = False
            for br in bottom_rects_x_list[k]:
                if br['x0'] <= (sum(c)/2) <= br['x1']:
                    limited = True
            if not limited:
                i = last_columns[k][j]
                columns_to_continue.append((k, i, j))
    return columns_to_continue


def fix_page_separated_table_cells(tables, bottom_rects_x_list, columns, last_columns, page_has_header):
    columns_to_continue = get_columns_to_continue(tables, bottom_rects_x_list, columns, last_columns)
    for ctc in tqdm(columns_to_continue, desc="Fix page-separated table cells [1/2]", leave=False):
        k, i, j = ctc
        first_row_index = 1 if page_has_header[k] else 0
        if tables[k][i][j] and tables[k+1][first_row_index][j]:
            common_str = shortest_combination(
                tables[k][i][j], tables[k+1][first_row_index][j])
            tables[k][i][j] = common_str
            tables[k+1][first_row_index][j] = common_str
        if tables[k][i][j] and (not tables[k+1][first_row_index][j]):
            tables[k+1][first_row_index][j] = tables[k][i][j]
    for ctc in tqdm(columns_to_continue[::-1], desc="Fix page-separated table cells [2/2]", leave=False):
        k, i, j = ctc
        first_row_index = 1 if page_has_header[k] else 0
        if (not tables[k][i][j]) and tables[k+1][first_row_index][j]:
            tables[k][i][j] = tables[k+1][first_row_index][j]
    return tables


def split_merged_table_cells(tables, tables_cells, rows, columns):
    for k in tqdm(range(len(tables)), desc="Split merged table cells", leave=False):
        big_cells = set()
        for t in tables_cells[k]:
            for i, r in enumerate(t.rows):
                for j, c in enumerate(r.cells):
                    standart_c = (columns[k][j][0], rows[k][i]
                                  [1], columns[k][j][1], rows[k][i][1])
                    if c is None:
                        for big_cell in big_cells:
                            if cell_in_cell(standart_c, big_cell[0]):
                                # print('FOUND CONTINUATION OF CELL!', k, i, j)
                                tables[k][i][j] = big_cell[1]
                    else:
                        if not cell_in_cell(c, standart_c):
                            big_cells.add((c, tables[k][i][j]))
    return tables


def unite_columns(table, i):
    new_table = []
    for t in table:
        new_t = t[:i] + [shortest_combination(t[i], t[i+1])] + t[i+2:]
        new_table.append(new_t)
    return new_table


def has_header(header, table):
    for t, h in zip(table[0], header):
        if t != h:
            return False
    return True


def main(input_file_name, output_file_name):
    tables = []
    tables_cells = []
    bottom_rects_x_list = []
    page_rects_y = None
    header = None
    page_has_header = []

    with pdfplumber.open(input_file_name) as pdf:
        for page_index, page in tqdm(enumerate(pdf.pages), desc="Read PDF pages", leave=False):
            if page_index == 0:
                page_rects_y = get_y_lines(page)
            page_rects_x, bottom_rects_x = get_x_lines(page)
            table_settings = {
                "vertical_strategy": "explicit",
                "explicit_vertical_lines": page_rects_y,
                # "vertical_strategy": "text",
                "horizontal_strategy": "explicit",
                # add line in the end to always have border in the bottom
                "explicit_horizontal_lines": page_rects_x,
            }
            table = page.extract_table(table_settings=table_settings)
            if page_index == 0:
                while any([not c for c in table[0]]):
                    for i in range(len(table[0])):
                        if table[0][i]:
                            continue
                        if i == 0:
                            page_rects_y = page_rects_y[:1] + page_rects_y[2:]
                            break
                        elif i == len(table[0]) - 1:
                            page_rects_y = page_rects_y[:-2] + page_rects_y[-1:]
                            break
                        minus_counter, plus_counter = 0, 0
                        for j in range(len(table)):
                            minus_counter += int(not table[j][i-1])
                            plus_counter += int(not table[j][i+1])
                        if plus_counter > minus_counter:
                            page_rects_y = page_rects_y[:i+1] + page_rects_y[i+2:]
                        else:
                            page_rects_y = page_rects_y[:i] + page_rects_y[i+1:]
                        break
                    table_settings["explicit_vertical_lines"] = page_rects_y
                    table = page.extract_table(table_settings=table_settings)
                header = table[0]
                page_has_header.append(True)
            else:
                page_has_header.append(has_header(header, table))
            tables.append(table)
            tables_cells.append(page.find_tables(table_settings=table_settings))
            bottom_rects_x_list.append(bottom_rects_x)
    rows, columns, last_columns = get_rows_and_columns(tables, tables_cells)
    tables = fix_page_separated_table_cells(tables, bottom_rects_x_list, columns, last_columns, page_has_header)
    tables = split_merged_table_cells(tables, tables_cells, rows, columns)

    table = sum([t[(1 if page_has_header[k] else 0):] for k, t in enumerate(tables)], [])
    table = [t for t in table if any(t)]
    table_pd = pd.DataFrame(table)
    table_pd.to_csv(output_file_name, header=header, index=False)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 script.py <input_file_name> <output_file_name>")
        sys.exit(1)  # Exit the script with an error code 1
    input_file_name = sys.argv[1]
    output_file_name = sys.argv[2]
    debug=False
    if debug:
        main(input_file_name, output_file_name)
    else:
        try:
          main(input_file_name, output_file_name)
        except Exception as e:
          print(input_file_name, output_file_name)
          print(str(e))
