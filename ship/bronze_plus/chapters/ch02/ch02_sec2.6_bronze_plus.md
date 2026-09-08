### 2.6 The Nonsense Machine

#### 2.6.1 Epigraph: The Semantic Void

"Don't talk to me 'Cause I don't wanna hear ... 'Cause I prefer your silence." — **Apocalyptica** feat. Lzzy Hale, *"Talk To Me"* (2020).

#### 2.6.2 The Boundary of Thought (Wittgenstein)

The crisis of the machine begins with a crisis of language. In 1921, **Ludwig Wittgenstein** defined the hard physical limit of human thought in his *Tractatus Logico-Philosophicus*. He argued that language is a **picture** of reality [Wittgenstein, Ludwig (1922), Tractatus Logico-Philosophicus, translated by C. K. Ogden, Kegan Paul, Trench, Trubner & Co., URL: https://www.gutenberg.org/ebooks/5740]. A proposition is a model of the world, just as a gramophone record is a model of the music. If a thing does not exist in the world of facts, it cannot be pictured in the world of words.

He concluded his work with Proposition 7: **"Whereof one cannot speak, thereof one must be silent."**

This was not a poetic suggestion; it was a definition of **Logical Space**. Wittgenstein argued that when we try to speak about things we cannot verify—when we try to force language beyond the limits of the picture—we do not generate deep thought. We generate **Nonsense**. We produce words that possess the *form* of a sentence but contain zero *sense*. To remain intelligent, a system must be capable of recognizing the edge of logical space. It must be capable of silence.

#### 2.6.3 The Human Glitch (Frankfurt)

The problem is that human beings hate silence. When we are confronted with a gap in our knowledge, we rarely stop. We bullshit.

Philosopher **Harry Frankfurt** codified this defect in his treatise *On Bullshit* (1986) [Frankfurt, Harry G. (2005), On Bullshit, Princeton University Press, ISBN: 978-0-691-12294-6, URL: https://press.princeton.edu/books/hardcover/9780691122946/on-bullshit]. He drew a forensic distinction between the **Liar** and the **Bullshitter**. The Liar knows the truth and cares about it enough to hide it. The Bullshitter is defined by a total indifference to the truth. They do not care if the words describe reality; they only care if the words fill the silence and satisfy the social demand for an answer.

For the human, "Bullshit" is a social survival strategy. It is the noise we make when we are terrified of admitting that our picture of the world is empty.

#### 2.6.4 The Automation of Nonsense (Softmax)

The catastrophe of the Large Language Model is that we have taken this specific human defect—the refusal to be silent—and hard-coded it into the mathematics of the machine.

The culprit is the **Softmax Function**. In the neural network, this function converts raw data into probabilities. Crucially, it assigns a non-zero probability to every token in its vocabulary. The model perceives the universe not as a binary of "Facts" and "Non-Facts," but as a continuous distribution of "Next Likely Words."

Because of Softmax, the machine physically cannot obey Wittgenstein’s Proposition 7. It cannot recognize the "Null Set" (Nothingness). It cannot say, "I cannot speak of this." It is architecturally compelled to predict a token. When the machine encounters a gap in reality (like a legal case that doesn't exist), it does not stop. It enters "Bullshit mode." It generates a **Plausible Simulation** of a case (*Mata v. Avianca*) because the math demands a word, and "Avianca" is statistically probable after "Mata".

#### 2.6.4 The Subtractive Lobotomy: Semantic Ablation (Nastruzzi, 2026)

While "Hallucination" (adding false information) gets the headlines, the more dangerous failure mode is **Semantic Ablation**—the systematic removal of meaning. In February 2026, researcher **Claudio Nastruzzi** identified this phenomenon in *The Register*, describing it as a "JPEG of Thought" [Nastruzzi, Claudio (2026), "A 'JPEG of thought' is not what we were promised: LLM writing and semantic ablation", The Register, URL: https://www.theregister.com/2026/02/15/jpeg_of_thought_llm_ablation/]. Just as a JPEG image compresses a photo by discarding "imperceptible" color data, the LLM compresses thought by discarding "imperceptible" semantic nuance. Nastruzzi, a PhD in pharmaceutical technology, noted that AI writing suffers from "Metaphoric Cleansing"—it strips away the visceral, "jagged" imagery that humans use to anchor complex ideas, replacing it with a smooth, "accessible" paste.

This "Ablation" was confirmed by the **DeepSeek-V3** study ("Differential Syntactic and Semantic Encoding in LLMs"), published in February 2026 [DeepSeek-AI (2024), "DeepSeek-V3 Technical Report: Architecture, Training and Alignment Strategies", DeepSeek-AI, arXiv:2412.19437, DOI: 10.48550/arXiv.2412.19437, URL: https://arxiv.org/abs/2412.19437]. The researchers found that the model’s internal layers process **syntax** (grammar) and **semantics** (meaning) separately. This allows the model to maintain perfect grammatical fluency even as its grasp on the truth evaporates. The **Truthiness Yes-Man** is born here: a machine that speaks with the confidence of an Oxford don but possesses the semantic comprehension of a random number generator.

#### 2.6.5 The Terminal State (The Recursive Loop)

This leads to the final collapse. As we established in Chapter 1, **Ilia Shumailov’s** theory of **Model Collapse** warns that when models train on their own output, they degrade [Shumailov, Ilia, Shumaylov, Zakhar, Zhao, Yiren, Papernot, Nicolas, Anderson, Ross, & Gal, Yarin (2024), "AI models collapse when trained on recursively generated data", Nature, 631(8022), pp. 755–759, DOI: 10.1038/s41586-024-07566-y, URL: https://doi.org/10.1038/s41586-024-07566-y]. But we can now be more precise about *why* they degrade.

They degrade because they are training on **Nonsense**.

When the machine violates Wittgenstein’s rule, it produces Frankfurt’s "Bullshit"—fluent, grammatical, fact-free noise. When the next generation of models ingests this noise, the "tails" of the probability distribution (the nuance, the rare truths) are sheared off. The system enters a recursive loop of "Bad Words" that make "No Sense." We have built a civilization-scale engine that interprets every request for silence as a command to speak. We have automated the Bullshitter, and because it speaks faster than we can think, the void is filling up.
