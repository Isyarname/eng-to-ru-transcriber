# Transliteration Rules DSL

This document describes the Domain-Specific Language (DSL) used to define IPA-to-Cyrillic transliteration rules.

## 📄 File Structure

Rules are defined in `src/eng_to_ru_transcriber/data/transliteration_rules.py` as two Python variables:

```python
macros = {
    "KEY": "value",
}

rules = '''
LHS->RHS
'''
```

The file is loaded at runtime via `importlib` — it is treated as **data**, not as executable code.

## 📦 Macros

Macros are key-value pairs where the key is a short token used in rules, and the value is the string it expands to:

```python
_ACCENT = '\u0301'

macros = {
    "C": "[бкдфгхлмнпрствжзнйш]",
    "V": "[аиоуэ]",
    "I": "[яиёюе]",
    "J": "[яёюе]",
    "'": _ACCENT,
}
```

The compiler performs simple string replacement for each macro key in both LHS and RHS of every rule. Longer keys are expanded first to avoid partial matches.

If a macro value is a Python `set`, it is automatically converted to a bracket group:

```python
macros = {
    "VOWELS": {"a", "e", "i", "o", "u"},  # becomes [aeiou]
}
```

## 📜 Rules Syntax

### Basic rule format

```
LHS->RHS
```

- `LHS` — left-hand side (pattern to match), **no spaces allowed**
- `->` — separator (spaces around it are ignored)
- `RHS` — right-hand side (replacement), **no spaces allowed**

Examples:
```
b->б
k->к
θ->ф
ð->д
```

### Multiple rules per line

Multiple rules can be placed on a single line, separated by whitespace:

```
ɟ->gʲ  ç->xʲ  ɲ->ŋʲ  c->kʲ
```

This is equivalent to:
```
ɟ->gʲ
ç->xʲ
ɲ->ŋʲ
c->kʲ
```

### Bracket groups

The DSL supports two kinds of bracket groups, both expanded by the compiler into separate rules:

**Square brackets `[abc]`** — alternatives of single characters:
```
[abc]->[xyz]
```
Expands to:
```
a->x
b->y
c->z
```

**Round brackets `(a|b|c)`** — alternatives of any length:
```
oi(xt|rs|rt|rh|s)->o(xt|rs|rt|rh|s)
```
Expands to:
```
oixt->oxt
oirs->ors
oirt->ort
oirh->orh
ois->os
```

### Parallel expansion

When a rule contains multiple bracket groups, they are expanded independently, producing all possible combinations:

```
[ab][cd]->[xy][zw]
```

Expands to four rules:
```
ac->xz
ad->xw
bc->yz
bd->yw
```

If RHS has fewer alternatives than LHS, RHS is duplicated:

```
[abc]->y
```

Expands to:
```
a->y
b->y
c->y
```

**Rule:** the number of alternatives in LHS and RHS must match, or RHS must have exactly one alternative (which is duplicated). Otherwise, an error is raised.

### Multi-character rules

Rules can match sequences of characters:

```
ʤ->дж
ʲа->я
ʲи->и
ʲо->ё
ʲу->ю
ʲэ->е
```

### Combining macros and bracket groups

Macros and bracket groups can be combined in a single rule:

```
Cй[аоуэ]->Cъй[аоуэ]
```

After macro expansion:
```
[бкдфгхлмнпрствжзнйш]й[аоуэ]->[бкдфгхлмнпрствжзнйш]ъй[аоуэ]
```

Then expanded into separate rules for each combination.

## ⚙️ Rule Processing

### Order of operations

1. **Parse** — split rules by `->`, ignore spaces around separator, extract multiple rules per line
2. **Expand macros** — replace macro keys with their values (longest keys first)
3. **Expand brackets** — convert `[abc]` to `(a|b|c)` and generate all combinations
4. **Add capitalized variants** — duplicate rules with uppercase first letter (if applicable)


### Rule application order

Rules are applied **in the order they appear** in the `rules` string, from left to right and top to bottom. More specific rules should come before general ones:

```
ʲа->я     ← specific (palatalization + vowel)
ʲ->ь      ← general (palatalization alone)
```

## 🔀 Regex Passthrough

The DSL does not escape regex special characters — they pass through to the final pattern as-is. This allows using regex constructs directly when needed:

| Construct      | Meaning                       | Example                               |
|----------------|-------------------------------|---------------------------------------|
| `?`            | Optional                      | `ʲ?` — optional palatalization        |
| `*`, `+`       | Repetition                    | `[rnl]{2}` — exactly two characters   |
| `^`, `$`       | Anchors                       | `^sʲ->s` — only at word start         |
| `(?!...)`      | Negative lookahead            | `!ʲ` → `(?!ʲ)`                        |
| `\|`           | Alternation (inside `(...)`)  | `(xt\|rs\|rt)`                        |

