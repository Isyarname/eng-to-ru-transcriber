
macros = {
	"[V]": "[aeiouy]",
	"[C]":"[bcdfghklmnpqrstvwxz]",
	"[V']": "(ə|a|ɑː|æ|ʌ|uː|ʊ|ɪ|iː|ɒ|ɔː|e|ɜː)",
	"[Z']":"(b|d|g|v|z|ð|ʒ|m|n|ŋ|l|r|w)",
	"[!Z']":"[ptkfsθʃ]",
	"i?": "(i|)",
	"t?": "(t|)",
    "!ʲ": "(?!ʲ)",
    "_":""

}



rules = '''

j -> dʒ
[V]h$ -> [V]


[ABCDEFGHIJKLMNOPQRSTUVWXYZ] -> (ej|biː|siː|diː|iː|ef|dʒiː|ejtʃ|aj|dʒej|kej|el|em|en|oʊ|piː|kjuː|ɑː|es|tiː|juː|viː|dʌbəljuː|eks|waj|zed)

y[aeiou] -> j[aeiou]
ti[oa]n$ -> ʃən
[V]sion -> [V]ʒən
[C]sion -> [C]ʃən
[tc]ial$ -> ʃəl
ture$ -> tʃə
tech -> tek
core$ -> kɔː
[tc]ious -> ʃəs
micro -> majkro
^pre -> prɪ
igh->aj
gh->g
qu -> kw
^x[V] -> z[V]
x -> ks
sch -> sk
sc[eiy] -> s[eiy]
t?ch -> tʃ
sh -> ʃ
th -> θ
ph -> f
c[eiy] -> s[eiy]


[oeiu]re -> (ɔː|ɪ|aj|jʊ)ə
[aeiouy]r![V] -> (ɑː|ɜː|ɜː|ɔː|ɜː|ɜː)
all -> ɔːl
alk -> ɔːk
alm -> ɑːm
old -> oʊld
ind -> ajnd
a[uw] -> ɔː
ea[C] -> iː[C]
oa[C] -> oʊ[C]
ai[C] -> ej[C]
ou[C] -> aʊ[C]
ook -> ʊk
(oo|oe) -> uː
(ee|ie) -> iː


[aio][C]e$ -> (ej|aj|oʊ)[C]
[aio][C][V] -> (ej|aj|oʊ)[C][V]
[aio][C][V'] -> (ej|aj|oʊ)[C][V']
u[C]e -> juː[C]e
[aeiou][C]![V] -> [æeɪɒʌ][C]
[vs]e[sd]?$ -> [vs][sd]?
y -> i
e[wu] -> juː
n[gk] -> ŋ[gk]
kn -> n
gn -> n
mb -> m
c -> k
r -> ɹ

[szʃʒ]es$ -> [szʃʒ]ɪz

[Z']s$ -> [Z']z
[!Z']s$ -> [!Z']s

[td]ed$ -> [td]ɪd
[!Z']ed$ -> [!Z']t
[Z']ed$ -> [Z']d

[C]{2} -> [C]

'''
