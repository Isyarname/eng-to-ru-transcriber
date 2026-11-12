# Engineering Experiments & Decision Log

This document records failed experiments and architectural decisions to prevent repeating mistakes in the future.

---

## 1. Why eng-to-ipa and g2p_en were rejected

An attempt was made to implement a context-aware mode to resolve homographs (like *read* /riːd/ vs /rɛd/) and improve OOV (Out-of-Vocabulary) words. The idea was to delegate the EN → IPA step to an external G2P library (`eng_to_ipa`, and later `g2p_en`) instead of using the fast hybrid engine.

### The Input Text

```text
Yesterday, my boy read an amazing book about history, and today he reads it again. 
He usually says that the wind is blowing hard outside, but it is impossible to wind up this old clock anyway. 
Live and learn! People who live in London like to drink hot tea every day. 
In 2026, it is important to remember: the quick brown fox jumps over the lazy dog!
hawk tuah
ChatGPT
cringe vibe ghosting doomscrolling gaslighting rizz skibidi clickbait unsee 
microdosing pregame hatewatch unfollow photobomb slowburn standard softlaunch 
glowup shadowban brainrot delulu ship hungerish nonbinary textneck overthinker 
clout neurodivergent misinformation unsubclic dropshipping freelancing gigworker 
fintech sidehustle overshare bingewatch noob
Hello, URL!
software
white
parseXMLData
```

### Result: eng-to-ru-transcriber (hybrid engine)

**Verdict:** Perfect. Keeps punctuation, handles slang, reads abbreviations letter-by-letter.

```text
естэрдэй, май бой рэд эн амэйзинг бук абаут хистэри, энд тадэй хи ридз ит агэйн.
хи южли сэз дэт да уайнд из блоуинг хард аутсайд, бат ит из импасабл ту уайнд ап дис оулд клак эниуэй.
лайв энд лэрн! пипл ху лайв ин ландан лайк ту дринк хат ти эври дэй.
ин 2026, ит из импортант ту римэмбэр: да куик браун факс джампс оувэр да лэйзи дог!
хок туа
чет-джи-пи-ти
криндж вайб гоустинг думскроулинг гэслайтинг риз скибиди кликбэйт анси́
майкроудозинг пригэйм хэйтуач анфалоу фоутоубам слоубэрн стэндэрд сафтлонч
глоуап шедоубэн брэйнрот дэлулу шип хангэриш нонбайнэри тэкстнэк оувэрфинкэр
клаут нуроудайвэрджент мисинфэрмэйшан ансабклик драпшипинг фрилэнсинг гигуэркэр
финтэк сайдхасл оувэршер бинджуач ну́б
халоу, ю-ар-эл!
софуэр
уайт
парс-экс-эм-эл-дэта
```

### Result: eng-to-ipa (transliterated)

**Verdict:** Flawed. Fails on OOV words and passes raw text to the IPA rules.

```
естардэй, май бой рэд ан амэйзинг бук абаут хистари, анд тадэй хи ридз ит агэн. хи южаули сиз дат да уинд из блоуинг хард аутсайд, бат ит из импасабл ти уинд ап дис оулд клак эниуэй. лив анд ларн! пипл ху лив ин ландан лайк ти дринк хат ти эвари дэй. ин 2026 ит из импортант ти римэмбар: да куик браун факс джампс оувар да лэйзи дог! хок туах кьхатгпт криндж вайб гхостинг доомскьроллинг гаслигхтинг ризз скибиди кликбэйт унсээ микьродосинг прэгамэ хатэуаткьх унфоллоу пхотобомб слоубурн стэндард софтлаункьх глоууп схадоубан браинрот дэлулу шип хунгэрисх нонбинарy тэхтнэкьк овэртхинкэр клаут нэуродивэргэнт мисинфармэйшан унсубкьликь дропсхиппинг фрилэнсинг гигуоркэр финтэкьх сидэхустлэ овэрсхарэ бингэуаткьх нооб хэлоу, урл! софуэр уайт парсэхмлдата
```

### Result: g2p-en (transliterated)

**Verdict:** Catastrophic. Failed on slang and generated nonsense like "нанбирани".

```text
естэрдэй , май бой рид эн амэйзинг бук абаут хистэри , анд тадэй хи ридз ит агэн . хи южаули сэз дэт да уайнд из блоуинг хард аутсайд , бат ит из импасабл ту уайнд ап дис оулд клак эниуэй . лайв анд лэрн ! пипл ху лайв ин ландан лайк ту дринк хат ти эвэри дэй . ин туэнти туэнтискайз , ит из импортант ту римэмбэр да куик браун факс джампс оувэр да лэйзи дог ! хок фаутфэкситинг вайб гоустинг думскроулминг гэслайтинг риз скибиди кликбэйт анси майкроудизам прагэйм хэйтуач анфоулоу фоутоубам слоубэрн стэндэрд софтлаунч глоуап шефоудан брэйнрат дэлул шип ханггэриш нанбирани тэкстнэкт оувэрфинкэр клаут нуроудживэрант мисинфэрмэйшан анскаблик драпшиф фрилэнсинг гигуэркэр финтэк сайдхауст оувэршер бинггуат нубэлоу , эрл ! софтуэрсфатэстрам
```

### Lessons Learned

1. **`eng-to-ipa` fails on OOV words.** For unknown words (like *unsubclic* or *ChatGPT*), it passes through the **raw English text** instead of generating phonemes. When this raw text hits the IPA-to-Cyrillic rules, the engine treats English letters as IPA symbols, leading to absurdities (e.g., the letter `c` is treated as IPA `/c/` and becomes `кь`).
2. **`g2p-en` hallucinates and destroys punctuation.** It ignores spaces and punctuation entirely, merging words together (*software white* -> *софтуэрсфатэстрам*). It also hallucinates on unknown words (e.g., *nonbinary* -> *нанбирани*).