#

TESS_LANG = jpn
TESS_FONT = IPAGothic
TESS_DATA = tessdata
TESS_DAT2 = data

TESS_EXP0 = $(TESS_LANG).$(TESS_FONT).exp0

#

all: combine

clean:
	rm -f \
		$(TESS_LANG).traineddata \
		$(TESS_EXP0).box \
		$(TESS_EXP0).tr \
		$(TESS_EXP0).txt \
		unicharset \
		$(TESS_LANG).unicharset \
		shapetable \
		$(TESS_LANG).shapetable \
		pffmtable \
		$(TESS_LANG).pffmtable \
		inttemp \
		$(TESS_LANG).inttemp \
		normproto \
		$(TESS_LANG).normproto\
		frequent_words_list \
		words_list \
		jpn.config \
		jpn.font_properties \
		jpn.freq-dawg \
		jpn.word-dawg \
		jpn.unicharambigs

combine: $(TESS_LANG).traineddata

#TODO: incomplete
uncombine:
	combine_tessdata \
		-u $(TESS_LANG).traineddata \
		.
	dawg2wordlist \
		$(TESS_LANG).unicharset \
		$(TESS_LANG).freq-dawg" \
		$(TESS_LANG).frequent_words_list

generate: $(TESS_EXP0).tiff

#

$(TESS_EXP0).tiff $(TESS_EXP0).box:
	./generate_img.py

#

frequent_words_list: $(TESS_DAT2)/wiktionary
	cp $(TESS_DAT2)/wiktionary frequent_words_list

words_list: \
		$(TESS_DAT2)/wiktionary \
		$(TESS_DAT2)/internet-jp.num \
		$(TESS_DAT2)/internet-jp-forms.num
	cat \
		$(TESS_DAT2)/wiktionary \
		$(TESS_DAT2)/internet-jp.num \
		$(TESS_DAT2)/internet-jp-forms.num \
		| uniq \
		> words_list

$(TESS_LANG).config: $(TESS_DATA)/$(TESS_LANG).config
	cp $(TESS_DATA)/$(TESS_LANG).config $(TESS_LANG).config

$(TESS_LANG).font_properties: $(TESS_DATA)/$(TESS_LANG).font_properties
	cp $(TESS_DATA)/$(TESS_LANG).font_properties $(TESS_LANG).font_properties

$(TESS_LANG).unicharambigs: $(TESS_DATA)/$(TESS_LANG).unicharambigs
	cp $(TESS_DATA)/$(TESS_LANG).unicharambigs $(TESS_LANG).unicharambigs

#

$(TESS_LANG).traineddata: \
		$(TESS_LANG).unicharset \
		$(TESS_LANG).shapetable \
		$(TESS_LANG).pffmtable \
		$(TESS_LANG).inttemp \
		$(TESS_LANG).normproto \
		$(TESS_LANG).freq-dawg \
		$(TESS_LANG).word-dawg \
		$(TESS_LANG).config \
		$(TESS_LANG).font_properties \
		$(TESS_LANG).unicharambigs
	combine_tessdata $(TESS_LANG).

#TODO: set up config so we can chose whether or not generate this file
# $(TESS_EXP0).box: $(TESS_EXP0).tiff
# 	tesseract \
# 		$(TESS_EXP0).tiff \
# 		$(TESS_EXP0) \
# 		batch.nochop \
# 		makebox


$(TESS_EXP0).tr: $(TESS_EXP0).box
	tesseract \
		$(TESS_EXP0).tiff \
		$(TESS_EXP0) \
		box.train.stderr

unicharset: $(TESS_EXP0).box
	unicharset_extractor \
		$(TESS_EXP0).box 

shapetable: $(TESS_LANG).font_properties unicharset $(TESS_EXP0).tr
	shapeclustering \
		-F $(TESS_LANG).font_properties \
		-U unicharset \
		$(TESS_EXP0).tr 

$(TESS_LANG).unicharset inttemp pffmtable: \
		$(TESS_LANG).font_properties \
		unicharset $(TESS_EXP0).tr \
		shapetable
	mftraining \
		-F $(TESS_LANG).font_properties \
		-U unicharset \
		-O $(TESS_LANG).unicharset \
		$(TESS_EXP0).tr

normproto: $(TESS_EXP0).tr
	cntraining $(TESS_EXP0).tr

# optional dictionaries

$(TESS_LANG).freq-dawg: frequent_words_list
	wordlist2dawg \
		frequent_words_list \
		$(TESS_LANG).freq-dawg \
		$(TESS_LANG).unicharset

$(TESS_LANG).word-dawg: words_list
	wordlist2dawg \
		words_list \
		$(TESS_LANG).word-dawg \
		$(TESS_LANG).unicharset

$(TESS_LANG).punc-dawg: puncs_list
	wordlist2dawg \
		puncs_list \
		$(TESS_LANG).punc-dawg \
		$(TESS_LANG).unicharset

$(TESS_LANG).number-dawg: numbers_list
	wordlist2dawg \
		numbers_list \
		$(TESS_LANG).number-dawg \
		$(TESS_LANG).unicharset

$(TESS_LANG).fixed-length-dawg: fixed-lengths_list
	wordlist2dawg \
		fixed-lengths_list \
		$(TESS_LANG).fixed-length-dawg \
		$(TESS_LANG).unicharset

$(TESS_LANG).bigram-dawg: bigrams_list
	wordlist2dawg \
		bigrams_list \
		$(TESS_LANG).bigram-dawg \
		$(TESS_LANG).unicharset

$(TESS_LANG).unambig-dawg: unambigs_list
	wordlist2dawg \
		unambigs_list \
		$(TESS_LANG).unambig-dawg \
		$(TESS_LANG).unicharset

#

#$(TESS_LANG).unicharset: unicharset
#	mv unicharset $(TESS_LANG).unicharset

$(TESS_LANG).shapetable: shapetable
	mv shapetable $(TESS_LANG).shapetable

$(TESS_LANG).pffmtable: pffmtable
	mv pffmtable $(TESS_LANG).pffmtable

$(TESS_LANG).inttemp: inttemp
	mv inttemp $(TESS_LANG).inttemp

$(TESS_LANG).normproto: normproto
	mv normproto $(TESS_LANG).normproto
