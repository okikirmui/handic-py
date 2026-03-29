# handic-py — Python wrapper for the HanDic MeCab dictionary

![PyPI - Version](https://img.shields.io/pypi/v/handic)

👉 **HanDic (dictionary) repository**: https://github.com/okikirmui/handic

`handic` is a **Python helper package** that makes it easy to use **HanDic**, a MeCab dictionary for contemporary Korean, **from Python code**.

> ⚠️ Important distinction  
> - **HanDic** = the MeCab dictionary itself (linguistic resource)  
> - **handic (this package)** = a Python interface / utility layer for HanDic  
>  
> The dictionary is developed and published separately;  
> this package focuses on *Python usability*.

---

# Overview

`handic` provides a convenient Python interface for the **HanDic Korean morphological analysis dictionary**.

It allows researchers and developers to perform **Korean morphological analysis from Python** without manually configuring dictionary paths or MeCab options.

The package:

- Bundles a snapshot of the HanDic dictionary
- Provides **high-level Python APIs**
- Handles **Jamo-based input/output**
- Supports **Hanja-aware representations**
- Works across **Linux, macOS, and Windows environments**

---

## Relationship between HanDic and this package

```
HanDic (dictionary repository)
        ↓
   MeCab dictionary files
        ↓
  handic (Python wrapper)
        ↓
  Your Python code
```

- The **linguistic design and dictionary entries** live in the HanDic repository
- This package bundles a released snapshot of the dictionary **only to enable Python use**
- Updates to dictionary content are driven by the HanDic project

---

## 🚀 Quick Start (Python)

### Installation

```bash
pip install handic mecab-python3 jamotools
```

### Minimal example

```python
import handic

text = "공기 진짜 좋다."

print(handic.tokenize_hangul(text))
print(handic.pos_tag(text))
print(handic.convert_text_to_hanja_hangul(text))
```

**Example output**
```
['공기06', '진짜', '좋다01', '다06', '.']
[('공기06', 'NNG'), ('진짜', 'MAG'), ('좋다01', 'VA'), ('다06', 'EF'), ('.', 'SF')]
空氣 眞짜 좋다.
```

---

## High-level API (Python convenience layer)

### `tokenize_hangul(text)`

Return a list of tokens in Hangul base form(Unified Hangul Code).

- Internally uses HanDic via MeCab
- Automatically restores Hangul syllables from Jamo
- Robust against unknown words

If you want to obtain tokens in surface form instead of base form, specify “surface” for the `mode` option.

example:

```python
text = "얼굴이 좋아 보여요."

handic.tokenize_hangul(text, mode="surface")
# ['얼굴', '이', '좋아', '보여', '요', '.']

handic.tokenize_hangul(text)
# ['얼굴01', '이25', '좋다01', '보이다02', '요81', '.']
```

---

### `tokenize(text)`

Return tokens in **Jamo surface form**.

- Low-level wrapper around MeCab

```python
text = "집에나 갈까?"

handic.tokenize(text)
# ['집', '에', '나', '가', 'ᆯ까', '?']
```

#### `tokenize()` vs `tokenize_hangul()`

- `tokenize()` returns **raw surface strings in Jamo form** from MeCab output.
- `tokenize_hangul(mode="surface")` returns **surface forms in composed Hangul** using the feature fields (7th feature).

In short, `tokenize()` preserves the original Jamo sequence, while `tokenize_hangul()` provides normalized Hangul strings.

##### Example

```python
# Jamo strings are longer because each Hangul syllable is decomposed
input = '말씀하시였다.'

print("tokenize()")
for item in handic.tokenize(input):
    print(f"{item} : {len(item)}")

print("tokenize_hangul(mode = 'surface')")
for item in handic.tokenize_hangul(input, mode="surface"):
    print(f"{item} : {len(item)}")
```

---

### `pos(text)` — lightweight POS

Return `(surface, coarse_pos)` pairs.

- Surface is returned in **Jamo surface form**
- POS corresponds to the first feature field

---

### `pos_tag(text)`
Return a list of `(token, POS)` tuples.

- Uses HanDic base forms(Unified Hangul Code) when available
- Falls back to surface forms for unknown words
- POS tags are based on the Sejong tag set(see https://docs.komoran.kr/firststep/postypes.html)

The following is an example for comparing `pos()` and `pos_tag()`.

```python
text = "집에서 놀았습니다."

handic.pos(text)
# [('집', 'Noun'), ('에서', 'Ending'), ('놀아', 'Verb'), ('ᆻ', 'Prefinal'), ('습니다', 'Ending'), ('.', 'Symbol')]

handic.pos_tag(text)
# [('집01', 'NNG'), ('에서02', 'JKB'), ('놀다01', 'VV'), ('ㅆ', 'EP'), ('습니다', 'EF'), ('.', 'SF')]
```

---

### `parse(text)`

Return raw MeCab output string.

- Includes all feature fields
- Intended for advanced use

```python
print(handic.parse("어디서 노나요?"))
```

output:

```
어디   Noun,代名詞,*,*,*,어디01,어디,*,*,A,NP
서    Ending,助詞,処格,*,*,서15,서,*,"에서02의 준말",*,JKB
노    Verb,自立,ㄹ語幹-脱落形,語基1,*,놀다01,노,*,*,A,VV
나요   Ending,語尾,終止形,*,1接続,나요,나요,*,"-나11",*,EF
?     Symbol,疑問符,*,*,*,?,?,*,*,*,SF
EOS
```

---

### `convert_text_to_hanja_hangul(text)`
Convert text into **mixed Hanja + Hangul** representation.

- Uses HanDic feature field (index 7)
- Preserves whitespace and punctuation
- Converts remaining Jamo into complete Hangul syllables

> ⚠️ **Caution**  
> 
> It may be possible to misidentifying homonyms. e.g. 자신: 自信/自身

---

## Platform compatibility (important update)

Recent versions of `handic` include a **more robust MeCab initialization layer** to improve cross‑platform compatibility.

Earlier versions could fail on **Windows or Conda environments** due to platform-specific path handling issues.

Typical errors included:

```
[ifs] no such file or directory: /dev/null
```

or failures caused by Windows path escaping when dictionary paths contained spaces.

### Improvements

The initialization logic now:

- Uses **`os.devnull` instead of `/dev/null`**
- Automatically **quotes dictionary paths**
- Normalizes Windows paths to **forward-slash format**
- Improves MeCab argument handling

These changes make the package more reliable on:

- Windows 10 / 11
- Miniconda / Anaconda environments
- Python installations where the dictionary path contains spaces

Most users **do not need to change their code**.

---

## Low-level access (for compatibility)

```python
import handic

print(handic.DICDIR)   # path to bundled HanDic snapshot
print(handic.VERSION)  # HanDic dictionary version
```

These are provided mainly for **backward compatibility** and inspection.

---

## Typical use cases

- Using HanDic conveniently from Python
- Korean corpus analysis and language education research
- Preprocessing Korean text for NLP pipelines
- Exploring Hangul / Hanja correspondences in contemporary Korean

---

## Features

Here is the list of features included in HanDic. For more information, see the [HanDic 품사 정보](https://github.com/okikirmui/handic/blob/main/docs/pos_detail.md).

  - 품사1, 품사2, 품사3: part of speech(index: 0-2)
  - 활용형: conjugation "base"(ex. `語基1`, `語基2`, `語基3`)(index: 3)
  - 접속 정보: which "base" the ending is attached to(ex. `1接続`, `2接続`, etc.)(index: 4)
  - 사전 항목: base forms(index: 5)
  - 표층형: surface(index: 6)
  - 한자: for sino-words(index: 7)
  - 보충 정보: miscellaneous informations(index: 8)
  - 학습 수준: learning level(index: 9)
  - 세종계획 품사 태그: pos-tag(index: 10)

---

## Citation

When citing **dictionary content**, please cite the HanDic project:

```
HanDic: morphological analysis dictionary for contemporary Korean
https://github.com/okikirmui/handic
```

When citing **this Python package**, please cite both the package and HanDic.

---

## License

This code is licensed under the MIT license. HanDic is copyright Yoshinori Sugai and distributed under the [BSD license](./LICENSE.handic). 

---

## Acknowledgment

This repository is forked from [unidic-lite](https://github.com/polm/unidic-lite) with some modifications and file additions and deletions.
