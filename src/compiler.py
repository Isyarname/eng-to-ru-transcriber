import itertools
import re

def parse(rules_str: str, transition_symbol="->") -> list:
    if not isinstance(rules_str, str):
        return []
    pattern = re.compile(r'(\S+)\s*' + re.escape(transition_symbol) + r'\s*(\S+)')
    prepared_rules = []
    for line in rules_str.strip().splitlines():
        matches = pattern.findall(line)
        if not matches:
            continue
        prepared_rules.extend(list(matches))
    return prepared_rules

def expand_contractions(rule: list, contractions: dict) -> list:
    items = contractions.items() if isinstance(contractions, dict) else contractions
    sorted_contractions = sorted(items, key=lambda e: -len(e[0]))
    
    new_rule = []
    for part in rule:
        for old, new in sorted_contractions:
            if isinstance(new, set):
                new = f"[{''.join(sorted(new))}]"
            if isinstance(new, str):
                part = part.replace(old, new)
        new_rule.append(part)
    return new_rule

def replace_brackets(text: str) -> str:
    classes = re.findall(r"\[(.*?)\]", text)
    for c in classes:
        text = text.replace(f"[{c}]", f"({ '|'.join(c) })")
    return text

def expand(rule: list[str]) -> list[tuple[str, str]]:
    rule1, rule2 = [replace_brackets(part) for part in rule]
    pattern = r"\((?!\?)(.*?)\)"
    if "(" not in rule2:
        matches1 = re.findall(pattern, rule1)
        if len(matches1) == 1:
            rule2 = f"({rule2})"
            
    parts1 = re.split(pattern, rule1)
    parts2 = re.split(pattern, rule2)
    if len(parts1) != len(parts2):
        raise ValueError(f"Строки имеют разное количество скобочных групп: {rule}")
    
    aligned_parts1 = []
    aligned_parts2 = []
    for i in range(len(parts1)):
        if i % 2 == 0:
            aligned_parts1.append([parts1[i]])
            aligned_parts2.append([parts2[i]])
        else:
            opts1 = parts1[i].split("|")
            opts2 = parts2[i].split("|")
            if len(opts2) <= 1 and len(opts1) > 1:
                opts2 = opts2 * len(opts1)
            elif len(opts1) != len(opts2):
                raise ValueError(f"Невозможно сопоставить варианты в группе {i//2 + 1}")
            aligned_parts1.append(opts1)
            aligned_parts2.append(opts2)
            
    combs1 = itertools.product(*aligned_parts1)
    combs2 = itertools.product(*aligned_parts2)
    return [("".join(c1), "".join(c2)) for c1, c2 in zip(combs1, combs2)]

def is_capitalizable_letter(char: str) -> bool:
    if not (char.isalpha() and char.islower()):
        return False
    code = ord(char)
    if 0x0250 <= code <= 0x02AF: return False
    if 0x1D00 <= code <= 0x1D7F: return False
    if 0x1D80 <= code <= 0x1DBF: return False
    return True

def add_capitalized_pairs(pairs: list) -> list:
    capitalized = []
    for L, R in pairs:
        if L and R and len(L) > 0 and is_capitalizable_letter(L[0]):
            L_cap = L[0].upper() + L[1:]
            R_cap = R[0].upper() + R[1:] if (len(R) > 0 and is_capitalizable_letter(R[0])) else R
            capitalized.append((L_cap, R_cap))
    return capitalized + pairs

def compile(rules_str: str, contractions: dict, add_capitalized=True) -> list:
    """
    🌟 ГЛАВНАЯ ЧИСТАЯ ФУНКЦИЯ МОДУЛЯ.
    Принимает сырую строку правил и словарь макросов. 
    Возвращает готовый плоский список кортежей замен.
    """
    parsed_pairs = parse(rules_str)
    
    if contractions:
        parsed_pairs = [expand_contractions(pair, contractions) for pair in parsed_pairs]
        
    expanded_rules = []
    for pair in parsed_pairs:
        expanded_rules.extend(expand(pair))
        
    if add_capitalized:
        expanded_rules = add_capitalized_pairs(expanded_rules)
        
    return expanded_rules
