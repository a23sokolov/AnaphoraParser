# AnaphoraParser
  Is programm module for anaphora resolution based on morphological, syntactic and collocation knowledge. It has been proven 
  to be efficient by a set of experiments. Current Module consist of 3 undependencies part: SyntaxTraining(syntag_to_malt),
  SyntaxParsing(sentence_to_malt), Anaphora(ml_anaphora).

### 1. SyntaxTrainig(syntag_to_malt)
  This module was written to translate [SyntagRus](http://www.ruscorpora.ru/instruction-syntax.html) data in [malttab](http://stp.lingfil.uu.se/~nivre/research/MaltXML.html) format. 
  Which use in [MaltParser](http://maltparser.org/) to learn classifier, how work with text on russian language. Small definition: SyntagRus is a treebank(syntax marked plain text with, morph description). 
  For more information how translation is done, try to read head of [this file](source/syntag_to_malt/syntagrus.py). More information how work with MaltParser also may see [here](https://habrahabr.ru/post/148124/).

### 2. SyntaxParsing(sentence_to_malt)
 Here you could see module to translate plain text in maltparser format with tmp results. Tmp results maybe used 
 to another calculation. So, for appropriate work Syntax classifier, morph description of words should be the same, as in SyntaxTraining. 
 As a result was fallen accuracy of morph definition from [pymorphy2](https://pymorphy2.readthedocs.io/en/latest/) to SyntagRus.
 [More information](source/sentence_to_malt/maltparser_translater.py)
 
### 3. Anaphora(ml_anaphora)
  Two previous modules was realised to alive this classifier. Here you can see Anaphora classifier for pronouns, which would be added in [npro_sample](source/config.py).
  Classifier training on anaphora marked text - RefText, and save model. For work with Anaphora Classifier may use prepared [model](source/ml_anaphora/model/)
  

###### Config
  Don't forget update path in [config](source/config.py).

