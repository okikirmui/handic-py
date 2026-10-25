# NK-HanDic Integration Testing

## Dictionary

| Item | Value |
|---|---|
| Repository | https://github.com/okikirmui/nkhandic |
| Release | NK-HanDic version 20260903 |
| Release page | https://github.com/okikirmui/nkhandic/releases |
| Archive filename | NK-HanDic_v20260903.zip |
| Archive SHA256 | 6140ecb6b73bcde8b75ee483a380fa98e885e49eb649c08d0677883d1e5c66a5 |
| Dictionary charset | utf8 |
| Dictionary entries | 221629 |

The SHA256 above identifies the downloaded archive, not the extracted
`sys.dic` file.

## Test Environment

| Item | Value |
|---|---|
| Test date | 2026/10/25 |
| OS / WSL distribution | Windows 11 / Debian 13 on WSL 2 |
| Python | 3.13.15 |
| mecab-python3 | 1.0.12 |
| jamotools | 0.1.10 |
| handic source commit | 98c9387 |
| Local dictionary directory | /home/yoshi/dictionaries/NK-HanDic |

Collect environment information using:

```bash
cat /etc/os-release
python --version
python -m pip show mecab-python3 jamotools
git rev-parse HEAD
```

The source commit identifies the implementation tested before committing
these integration tests.

## Running the Tests

Set the directory that directly contains `sys.dic`:

```bash
export NKHANDIC_DICDIR="$HOME/dictionaries/NK-HanDic"
```

Run the integration tests:

```bash
python -m pytest tests/test_nkhandic_integration.py -vv
```

Run the complete test suite with the external dictionary configured:

```bash
python -m pytest -q
```

The integration tests fail if `NKHANDIC_DICDIR` is unset or `sys.dic`
is missing. To run only the other tests:

```bash
python -m pytest -q --ignore=tests/test_nkhandic_integration.py
```

## Test Sentence

```text
총비서동지께서 말씀하시였다.
```

## Expected Results

### Base Forms and POS Tags

```python
[
    ("총비서", "NNG"),
    ("동지006", "NNG"),
    ("께서", "JKS"),
    ("말씀", "NNG"),
    ("하다02", "XSV"),
    ("시", "EP"),
    ("ㅆ", "EP"),
    ("다06", "EF"),
    (".", "SF"),
]
```

### Hangul Surface Tokens

```python
[
    "총비서",
    "동지",
    "께서",
    "말씀",
    "하",
    "시여",
    "ㅆ",
    "다",
    ".",
]
```

## Verification Method

- Confirmed that `dictionary_info().filename` points to the external
  NK-HanDic `sys.dic`.
- Checked base forms against feature index 5 (the sixth field).
- Checked POS tags against feature index 10 (the eleventh field).
- Checked surface tokens against the raw MeCab surface strings,
  with Jamo composed separately for each token.
- Preserved dictionary identifiers such as `동지006`, `하다02`,
  and `다06` in the expected base forms.
- Confirmed that the isolated surface Jamo `ᆻ` becomes `ㅆ`.

## Test Results

| Check | Result |
|---|---|
| External dictionary path and raw output inspected | PASS |
| Integration tests: 17 cases | PASS |
| Complete test suite | PASS |


## Scope and Limitations

These tests cover external dictionary selection, propagation through all
six high-level APIs, dictionary switching, and fixed expected outputs
for `pos_tag()` and `tokenize_hangul(mode="surface")`.

They do not establish Windows/Conda compatibility or comprehensive
linguistic accuracy. Other API outputs are compared between `dicdir`
and explicit `tagger` usage; they do not yet have independently checked
fixed expected values.

## Updating the Dictionary

When changing the dictionary release:

1. Record the new release, archive filename, and archive SHA256.
2. Inspect the raw output and dictionary features again.
3. Investigate any differences before changing expected values.
4. Run the integration tests and the complete test suite.
5. Update this document and the expected values together.
