import re
import math
from typing import Optional, Tuple


def vn_words_to_num(text: str) -> Optional[int]:
    """Convert Vietnamese number words into an integer."""
    digits = {
        'không': 0, 'một': 1, 'mốt': 1, 'hai': 2, 'ba': 3,
        'bốn': 4, 'tư': 4, 'năm': 5, 'lăm': 5, 'nhăm': 5, 'sáu': 6,
        'bảy': 7, 'bẩy': 7, 'tám': 8, 'chín': 9
    }
    tokens = text.lower().strip().split()
    total = 0
    subtotal = 0
    curr_digit = 0
    has_match = False

    for tok in tokens:
        if tok in digits:
            curr_digit = digits[tok]
            has_match = True
        elif tok in ['mười', 'mươi']:
            if curr_digit == 0:
                subtotal += 10
            else:
                subtotal += curr_digit * 10
            curr_digit = 0
            has_match = True
        elif tok == 'trăm':
            if curr_digit == 0:
                subtotal += 100
            else:
                subtotal += curr_digit * 100
            curr_digit = 0
            has_match = True
        elif tok in ['nghìn', 'ngàn']:
            subtotal += curr_digit
            curr_digit = 0
            if subtotal == 0:
                subtotal = 1
            total += subtotal * 1000
            subtotal = 0
            has_match = True
        elif tok == 'triệu':
            subtotal += curr_digit
            curr_digit = 0
            if subtotal == 0:
                subtotal = 1
            total += subtotal * 1000000
            subtotal = 0
            has_match = True
        elif tok == 'tỷ':
            subtotal += curr_digit
            curr_digit = 0
            if subtotal == 0:
                subtotal = 1
            total += subtotal * 1000000000
            subtotal = 0
            has_match = True
        elif tok in ['linh', 'lẻ']:
            curr_digit = 0
        elif tok.isdigit():
            curr_digit = int(tok)
            has_match = True

    if not has_match:
        return None
    return total + subtotal + curr_digit


def solve_math_query(query: str) -> Optional[str]:
    """
    Instantly parse and solve Vietnamese natural language arithmetic queries (< 0.5ms).
    Returns formatted natural Vietnamese answer or None if query is not math.
    """
    q = query.lower().strip()
    q = re.sub(r'[\?\.\!\,]+$', '', q).strip()
    q = re.sub(r'\s+(bằng mấy|bằng bao nhiêu|ra mấy|là bao nhiêu|là mấy|thì bằng mấy|hết bao nhiêu)$', '', q)
    q = re.sub(r'^(tính|tính giúp|kết quả của|phép tính|cho tôi biết|cho em hỏi)\s+', '', q)

    # 1. Square root: e.g. "căn bậc hai của 64", "căn 81"
    sqrt_match = re.search(r'^(?:căn bậc hai của|căn bậc 2 của|căn của|căn)\s+(.+)', q)
    if sqrt_match:
        target = sqrt_match.group(1).strip()
        val = None
        if target.replace('.', '', 1).isdigit():
            val = float(target)
        else:
            w_val = vn_words_to_num(target)
            if w_val is not None:
                val = float(w_val)
        if val is not None:
            if val < 0:
                return "Không thể tính căn bậc hai của số âm."
            res = math.isqrt(int(val)) if val.is_integer() and math.isqrt(int(val))**2 == int(val) else round(math.sqrt(val), 4)
            val_str = str(int(val)) if val.is_integer() else str(val)
            return f"Căn bậc hai của {val_str} bằng {res}."

    # 2. Percentage: e.g. "20% của 500", "15 phần trăm của 200"
    pct_match = re.search(r'^(\d+(?:\.\d+)?)\s*(?:%|phần trăm)\s+(?:của)\s+(\d+(?:\.\d+)?)$', q)
    if pct_match:
        p = float(pct_match.group(1))
        base = float(pct_match.group(2))
        res = (p * base) / 100.0
        p_str = str(int(p)) if p.is_integer() else str(p)
        base_str = str(int(base)) if base.is_integer() else str(base)
        res_str = str(int(res)) if res.is_integer() else str(round(res, 4))
        return f"{p_str}% của {base_str} bằng {res_str}."

    # 3. Binary Operators (+, -, *, /, ^)
    ops = [
        (r'\s+(?:cộng với|cộng|thêm|\+)\s+', '+', 'cộng'),
        (r'\s+(?:trừ đi|trừ|bớt|\-)\s+', '-', 'trừ'),
        (r'\s+(?:nhân với|nhân|\*|x|lần)\s+', '*', 'nhân'),
        (r'\s+(?:chia cho|chia|\/|\:)\s+', '/', 'chia'),
        (r'\s+(?:mũ|lũy thừa|\^)\s+', '**', 'mũ')
    ]

    for pattern, sym, vn_op in ops:
        parts = re.split(pattern, q, maxsplit=1)
        if len(parts) == 2:
            left_s, right_s = parts[0].strip(), parts[1].strip()
            # Parse left & right operand
            left_val = float(left_s) if left_s.replace('.', '', 1).isdigit() else (float(vn_words_to_num(left_s)) if vn_words_to_num(left_s) is not None else None)
            right_val = float(right_s) if right_s.replace('.', '', 1).isdigit() else (float(vn_words_to_num(right_s)) if vn_words_to_num(right_s) is not None else None)

            if left_val is None or right_val is None:
                continue

            if sym == '+':
                res = left_val + right_val
            elif sym == '-':
                res = left_val - right_val
            elif sym == '*':
                res = left_val * right_val
            elif sym == '/':
                if right_val == 0:
                    return "Không thể chia cho số 0."
                res = left_val / right_val
            elif sym == '**':
                if right_val > 100:
                    return "Số mũ quá lớn để tính nhanh."
                res = left_val ** right_val

            l_str = str(int(left_val)) if left_val.is_integer() else str(left_val)
            r_str = str(int(right_val)) if right_val.is_integer() else str(right_val)
            res_str = str(int(res)) if res.is_integer() else str(round(res, 4))
            return f"{l_str} {vn_op} {r_str} bằng {res_str}."

    return None
