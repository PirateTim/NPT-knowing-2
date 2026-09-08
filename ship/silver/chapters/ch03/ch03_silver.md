# **Chapter 3: The Bucket Isn’t Empty**

"We are staggering releases because the economics of scaling are brutal."

— **Sam Altman**, CEO of OpenAI (2023)

"We project that high-quality language data will be exhausted by 2026."

— **Villalobos et al.**, Epoch AI (2022)

### **3.1 The Scarcity in the Flood: The IBM Precedent**

To understand the panic behind the "Data Shortage" of the AI era, we must first audit the receipts of the "Big Data" era. The most expensive epistemological failure of the twenty-first century did not occur because there was no information. It occurred because the information was trapped in a format that the machine could not digest, forcing its creators to replace reality with a simulation.

In October 2013, IBM announced a partnership with the M.D. Anderson Cancer Center that was marketed not as software, but as a messianic event. The goal was to train the **Watson Oncology Expert Advisor (OEA)** to eradicate leukemia. IBM sold the project on the premise of "cognitive abundance": Watson had ingested the entirety of PubMed and the relevant medical textbooks—a corpus of over 600,000 pieces of medical evidence. The plan was to marry this **Institutional Archive** with the vast repository of M.D. Anderson’s electronic patient records to create a god-like diagnostician. The initial estimate for the pilot was a modest $2.4 million.

But inside the data center, the engineers hit a wall that had nothing to do with computing power. They discovered that while the academic data (textbooks) was abundant, the training data (real patient histories) was functionally inaccessible. The problem was not that the records were on paper; the HITECH Act of 2009 had ensured they were digital. The problem was that they were semantic "Dark Matter". The vital clinical nuance—the reasoning behind a dosage change, the subtle reaction to a chemotherapy drug—was locked in "unstructured notes," PDF scans, and proprietary formats that Watson’s Natural Language Processing (NLP) could not parse without massive manual intervention. The "ingestion cost" of cleaning the data was not $2.4 million; it was an order of magnitude higher.

Faced with a functional shortage of usable ground truth, the engineers at Memorial Sloan Kettering (who were tasked with training the system) made a fatal decision. They stopped trying to force the machine to learn from the messy reality of actual survivors. Instead, they fed Watson "synthetic cases"—hypothetical patient profiles devised by human doctors to represent "ideal" cancer scenarios.

They trained the AI on a map, not the territory. This was **Epistemic Counterfeiting**. The result was a lethal decoupling from reality. Because Watson had learned from "perfect" synthetic data rather than the "messy" continuity of real-world biology, it could not handle the edge cases of actual life. In one documented failure, the system reviewed the file of a 65-year-old lung cancer patient who was already suffering from severe bleeding. Watson, operating on its synthetic logic, confidently recommended administering **Bevacizumab**—a drug whose primary contraindication is that it causes severe bleeding. The machine recommended a medical execution because it was data-starved. M.D. Anderson cancelled the project in 2016\. The final cost was not $2.4 million; it was $62 million. They had millions of records, but not a single drop of ground truth the machine could trust.

### **3.2 The Prophecy of the Vacuum**

The tragedy of the "Synthetic Patient" was not an isolated engineering error; it was the inevitable result of a vacuum that historian Daniel Boorstin identified fifty years earlier. In his 1961 seminal work *The Image*, Boorstin identified a structural flaw in the modern media age: the technology of distribution had outpaced the production of reality.

Boorstin noted that the machinery of the press—and later, the 24-hour news cycle—required a constant stream of input to justify its existence. When the supply of actual events (facts) ran dry, the system did not shut down. Instead, it manufactured what Boorstin called the **"Pseudo-Event"**: a simulation of news created solely to fill the void.

By the 1990s, this dynamic had consumed the information ecosystem. The "News Hole" of 24-hour cable demanded content regardless of whether anything had actually happened. The result was the "Talking Head"—a biological token generator designed to dilute a single hour of fact into twenty-three hours of speculation.

Today, Silicon Valley has industrialized this vacuum. They have built a computational container—the 13-trillion-token context window—that is orders of magnitude larger than the sum total of high-quality human knowledge. Like the cable producers of the 1990s, they have hit the hard limit of reality. And like the engineers at IBM Watson, they have decided that if they cannot find enough truth to fill the machine, they will simply lower the standards of what counts as input. The "Synthetic Patient" that killed the oncology project has metastasized into the "Synthetic Web" that feeds the Large Language Model.

### **3.3 The Industrialization of Memory**

To understand why the "Hoard" is so valuable, we must appreciate the effort of the tech companies to replicate it. The public face came in December 2004, when Google announced "Project Ocean" (later Google Books). The goal shifted from curation to ingestion.

Google’s "Project Ocean" was not a software project; it was a logistics operation that rivaled a military deployment. As documented by journalist James Somers in *The Atlantic*, Google didn't just ask libraries for their data; they backed 53-foot semi-trucks up to the loading docks of Harvard, Oxford, and the University of Michigan. They effectively vacuumed the physical knowledge of the 20th century into the server farms of the 21st.

Inside the scanning centers, the atmosphere was less "library" and more "assembly line." The books were placed in custom-built mechanical cradles designed to hold the spine at a precise angle to prevent cracking. As the pages were turned—often by human operators using foot pedals to keep their hands free to adjust the paper—they were bombarded by a sensor array that would make a self-driving car jealous. Google’s engineers had solved the problem of page curvature using LIDAR (Light Detection and Ranging). As the cameras captured the text, a laser grid mapped the 3-D geometry of the warped paper. Algorithms then "de-warped" the image, flattening the curled pages into perfectly rectilinear PDFs without ever breaking the book’s spine. They scanned at a rate of 1,000 pages per hour, per station.

For a decade, they digitized the "long tail" of human thought—the obscure treatises on 18th-century botany and the forgotten memoirs of Civil War soldiers. This was the "Hoard" in its rawest form: 25 million volumes of verified human effort, processed through infrared light and stored in a format that would eventually teach Gemini how to speak.

If Google is the Librarian who never threw anything away, Microsoft is the Tourist who got bored and left the museum. In 2006, Microsoft launched Live Search Books, a massive digitization initiative designed to rival Google’s "Project Ocean." For two years, they operated fleets of scanners in major research libraries, digitizing over 750,000 books and indexing 80 million journal articles.

They were building their own Hoard. Then, on May 23, 2008, they abruptly quit. In a blog post that now reads like a corporate suicide note, Microsoft announced they were shutting down the program because they believed the future of search was "commercial vertical search," not library indexing. They didn't just stop scanning; they removed the digitized books from their index and leaving the field entirely to Google.

### **3.4 The Witness: The Architecture of Memory**

For a decade before Google books The world's leading academic publishers had been scanning and producing a hoard of digitized science. I know the texture of this "Hoard" because I helped build it. From 2007 to 2012, I worked at Cambridge University Press, the world’s oldest publishing house. During that time, we undertook a project that felt less like data entry and more like religious observance: the digitization of Sir Isaac Newton’s original manuscripts and first editions.

To do this, we purchased a fleet of robotic scanners that had been discarded by Microsoft. These were the physical artifacts of their abdication—the hardware left behind when they shut down "Live Search Books" in May 2008\. While Google was busily creating an "ocean" of garbled, finger-stained scans with their industrial LIDAR rigs, we were operating a clean room. As my colleague Rufus showed me, the book was cradled at a 45-degree angle to minimize the pressure on the spine. The environment was light-controlled to prevent the aging of the ink. Two cameras, positioned like eyes, photographed the left and right pages simultaneously. Every few seconds, a precise puff of air would lift the next page, turning it without a human hand or a mechanical arm ever touching the precious artifact. This was Non-Destructive Digitization. It was slow, expensive, and reverent. It preserved the "Ground Truth" of the scientific revolution in high-fidelity.

But there is a distinction between the artifact and the container. Years earlier, in 2003, I worked on digitization for The Haworth Press, a scholarly publisher founded by Bill Cohen—a man whose proudest boast was not his catalog, but his ability to type 150 words per minute. There, the preservation of knowledge was equally meticulous with precise metadata records.

We worked in the physical basement of the printing building. We did not use air puffs or cradles. To digitize the backlist of journals and monographs, we physically cut the spines off the books and fed the loose pages into high-speed commercial hopper scanners. This was Destructive Digitization.

There was no moral stain here. Newton’s manuscripts are unique artifacts; a 1995 copy of the *Journal of Homosexuality* is a mass-produced industrial object. The book was consumed to create the PDF, and the PDF was the point. Ironically, this butchery became the only reason the knowledge survived. A few years later, a flood destroyed the Haworth warehouse. If we had relied on the "Redundant Physical Copies," the record would have been wiped clean. But because we had fed the books to the machine, the PDFs survived. When Taylor & Francis—one of the "Big Five" academic publishers—acquired Haworth, they didn't buy a library; they bought a hard drive. The "Digital Shadow" became the only reality.

**The Postscript: Project Panama**

I thought the Haworth destructive scanning was simply a tool of efficiency. I was wrong. It was a preview of a legal loophole. On January 27, 2026, the *Washington Post* revealed that Anthropic, the maker of Claude, had launched a secret initiative code-named "Project Panama". Their goal was to "destructively scan" nearly every book in existence.

They hired Tom Turvey, the former architect of Google Books, to run the operation. But unlike Google, they aren't scanning to create a searchable index. They are scanning to create a legal alibi.

The moral hang-up isn't about the destruction of the paper; it is about the "Format Shifting" defense. By buying a physical book, scanning it, and then immediately destroying the original, Anthropic argues they are not "copying" the work—they are simply moving their legally purchased property from a physical state to a digital state. The guillotine is their way of proving to a judge that two copies do not exist. They are burning the bridge to the past not out of malice, but to cover their tracks in court. The butchery I witnessed in a basement in 2003 is now the standard operating procedure for the most advanced AI lab on earth.

### **3.5 The Friction Paradox: The Exploding Book**

"We are paying three to five times the consumer price for licenses that expire."

— **Jennie Pu**, Director of Hoboken Public Library (February 2026\)

To understand the full legal audacity of "Project Panama," we must place it alongside the war the publishing industry has been waging against public libraries for fifteen years. This conflict is defined by a single, unwavering principle asserted by the publishers: **A digital file is not a book.**

Because a digital file does not degrade, the "Big 5" publishers (Penguin Random House, HarperCollins, Simon & Schuster, Hachette, Macmillan) successfully argued that the "First Sale Doctrine"—the right to lend or resell a book you bought—does not apply to pixels. They insisted that a library cannot "own" an ebook; it can only lease access to a service.

To enforce this distinction, they manufactured **Friction.**

In 2011, **HarperCollins** introduced the infamous "26-Loan Cap." The logic was that a physical paperback would fall apart after roughly 26 checkouts, so the digital file should "explode" (delete itself) after the same number of uses. This was the introduction of **Artificial Scarcity** into the library infrastructure.

This friction has a precise price tag. In **Hoboken, New Jersey**, Library Director Jennie Pu revealed in 2026 that her library is forced to pay **$60 to $80** for a single digital copy of a bestseller that a consumer can buy for $15 [DiFilippo, D. (2026), "DiFilippo, D.", URL: https://newjerseymonitor.com/2026/02/22/libraries-pay-5-times-more-for-e-books-than-consumers-n-j-lawmakers-want-to-change-that/]. Worse, this $80 fee is not a purchase; it is a rental payment for a license that evaporates after two years.

The math of this extraction is brutal. An audit of **Ocean County Library’s** 2024 budget shows a materials expenditure of **$5.68 million** [Ocean County Library (2024), "Adopted 2024 Ocean County Library Report", URL: https://theoceancountylibrary.org/sites/default/files/about/report/2024-report.pdf]. As the "Digital Rent" consumes a larger percentage of this budget, the library is forced into a "Zeno’s Paradox" of collection development: they are spending more money every year just to keep the collection from shrinking. According to data from **ReadersFirst**, the annualized cost of library ebooks has risen **six times faster** than the consumer retail price (ReadersFirst, 2025). A library pays roughly **$2.00 per checkout** for a digital file, while a physical paperback costs pennies per read.

When libraries tried to legislate their way out of this trap, the publishers crushed them in federal court. In 2022, in the case of **Association of American Publishers (AAP) v. Frosh**, a federal judge struck down a Maryland law that required "reasonable terms" for library licensing. The court ruled that federal copyright law preempts state law, affirming the publishers' exclusive right to dictate the terms of digital distribution.

The "Friction" campaign reached its legal zenith in 2024 with the ruling in **Hachette v. Internet Archive**. The court decisively ruled that **"Controlled Digital Lending"** (CDL)—the practice of buying a physical book, scanning it, and lending the digital file on a one-to-one ratio—is illegal. The judge declared that you cannot simply "format shift" a library collection to bypass the licensing market.

This brings us to the **Paradox of 2026**.

In February 2026, as **Senator Andrew Zwicker** introduced a bill in New Jersey to classify these restrictive library contracts as "consumer fraud" [DiFilippo, D. (2026), "DiFilippo, D.", URL: https://newjerseymonitor.com/2026/02/22/libraries-pay-5-times-more-for-e-books-than-consumers-n-j-lawmakers-want-to-change-that/], the AI industry was quietly executing the exact maneuver that the courts had just declared illegal for humans.

**Anthropic’s "Project Panama"** is nothing less than **Industrial-Scale Controlled Digital Lending**. By buying physical books, scanning them, and destroying the originals to claim "format shifting," Anthropic is relying on a legal theory that the publishers have spent millions of dollars to destroy.

The contradiction is fatal:

1. **The Library Reality:** If a library scans a book to lend it to a human, it is **Piracy**. The publisher argues that the digital file competes with the licensed market.  
2. **The AI Reality:** If an AI lab scans a book to lend it to a model, they claim it is **Fair Use**. They argue that the digital file is merely "internal data."

But the market reality is identical. Both the library and the AI are "consuming" the book to serve users. The contrast in scale is vertigo-inducing. While **Hoboken Public Library** fights to stretch a **$658,000** materials budget against a 500% markup, **OpenAI** announced in February 2026 that it had reset its infrastructure spending target to **$600 billion** by 2030 [Capoot, A., & Rooney, K. (2026), "Capoot, A., & Rooney, K.", URL: https://www.cnbc.com/2026/02/20/openai-resets-spending-expectations-600-billion-compute.html]. The entity spending nearly a trillion dollars on "compute" refuses to pay the entity spending pennies on "knowledge" for the right to use it. The industry has constructed a legal reality where a digital book is a "licensed service" when it serves the public good, but a "piece of property" when it serves a trillion-dollar model.

### **3.6 The Mathematics of Gluttony**

The central paradox of the AI era is that the richest entities in human history are currently pleading poverty. They are not asking for money; they are asking for words. In October 2022, a research team led by Pablo Villalobos at Epoch AI published a forecast that sent a tremor through the boardrooms of Silicon Valley. Their paper, **Will We Run Out of Data?**, offered a bleak Malthusian prediction: "We project that high-quality language data will be exhausted by 2026".

But this panic hides a specific accounting fraud. To understand the lie, we must audit the ledger. A frontier model like GPT-4 requires a "throughput" of roughly 13 trillion tokens to reach convergence. Yet, the standard benchmark for the "high-quality public web"—the C4 dataset (Colossal Clean Crawled Corpus)—contains only about 190 billion tokens.

This number is the smoking gun. It reveals that the "Clean Web" is actually smaller than the "Private Archive." The sequestered holdings of the "Big Five" academic publishers (The Licensed Repositories) contain an estimated 500 billion tokens of high-density fact. Do the math: The private reserve is nearly three times larger than the public commons.

The industry attempts to dismiss this ledger by citing the sheer scale of their hunger. They argue that a frontier model needs 13 trillion tokens, so a reserve of 500 billion is merely a drop in the bucket. This is a deception based on volume rather than density. Research from within Microsoft itself (specifically the Phi-1 *Textbooks Are All You Need* paper) has demonstrated a phenomenon we might call the 'Exchange Rate of Truth.' It turns out that one token of high-fidelity, verified textbook data is worth approximately 1,000 tokens of common web scrape in terms of model performance.

When you apply this multiplier, the 'Hoard' is not 4% of the requirement; it is a super-critical mass. They do not need 13 trillion tokens of sludge; they need a smaller amount of signal. They are choosing the sludge only because it is free.

### **3.7 The Alchemist's Bill**

"We are not running out of data. We are running out of free data. And the industry has decided that it is cheaper to burn the rainforest than to pay for the lumber."

This brings us to the most damning calculation in the ledger: The Alchemist's Bill. The industry argues that licensing the "Hoard" is economically impossible. But this defense crumbles when we look at their capital expenditures (CapEx).

In 2024 alone, the major AI labs committed over $100 billion to Nvidia for H100 GPUs. They are securing energy deals to reopen nuclear power plants to power these chips. They are building the most expensive infrastructure in human history. Why? A significant portion of this compute is not being used to serve customers; it is being used to clean the data. Because they refuse to license the pristine "Hoard," they are forced to scrape the polluted "Wild Web."

Do the math on the waste:

* **Option A (The Licensing Model):** They could pay a global licensing fee of roughly $10-20 billion annually to the world’s major publishers and archives. This would secure a direct pipeline to the 500 billion tokens of high-density, clean fact. The "Filtering Cost" would be near zero.  
* **Option B (The Alchemist Model):** Instead, they are spending $100 billion+ on hardware and energy to ingest trillions of tokens of low-quality garbage, hoping that if they cook it hot enough, it will distill into truth.

They are spending ten dollars on the "Pan" (GPUs) to find one dollar’s worth of "Gold" (Signal), solely to avoid paying five dollars to the mine owner.

### **3.8 The Flood of Slop**

The final defense of the Silicon Valley engineer is the Theology of Scale. They argue that the quality of the data matters less than the volume. They believe that if the "Slop" is large enough—13 trillion, 100 trillion, a quadrillion tokens—the model will magically develop the capacity to discern truth from noise.

This is **Epistemological Nihilism**. It assumes that "Truth" is simply the most statistically probable sentence. But the internet is not a democracy of facts; it is a tyranny of engagement. A lie that is repeated one million times in the Common Crawl has a higher "statistical weight" than a truth buried in a single PDF behind an Elsevier paywall. By optimizing for scale, they have built a machine that does not check for accuracy; it checks for popularity.

### **3.9 The Pile: "We Are Just Reading"**

To understand the sheer velocity of the moral reversal, we must look at the bodies left behind by the previous regime. If we were to stack the victims of the Copyright Wars into a single pile, the diversity of the casualties would be disorienting.

At the bottom of the pile, we find Sarah Seabury Ward, a 66-year-old grandmother from Massachusetts. In 2003, the Recording Industry Association of America (RIAA) sued her for being a "digital gangster," alleging she had shared thousands of rap songs on Kazaa. It didn't matter that she owned a Macintosh (which couldn't run Kazaa) or that she had never heard of the songs. The industry needed to make an example of a civilian to protect the sanctity of the file.

In the middle of the pile, we find Aaron Swartz. A child prodigy and co-founder of Reddit, Swartz believed that scientific knowledge should be a public good. In 2011, he connected a laptop to the MIT network and downloaded millions of academic articles from JSTOR—the very "Hoard" we discussed earlier. He didn't sell them. He didn't profit. He intended to liberate them. For this act of "theft," federal prosecutors threatened him with 35 years in prison. Crushed by the weight of the state, he took his own life at the age of 26\.

Near the top, we find Kim Dotcom. A flamboyant pirate who ran Megaupload, Dotcom provided the locker for the same copyrighted reality that Swartz tried to liberate. In 2012, the FBI raided his New Zealand mansion with helicopters and counter-terrorism units. His assets were frozen, his servers seized, and his life dismantled for hosting the very movie files and textbooks that are now standard training data.

Now, look at 2026\. The leaders of the AI industry have done exactly what Aaron Swartz did, but on a scale that defies comprehension. Swartz downloaded a few million articles; OpenAI and Google have downloaded everything. They have scraped the JSTOR archives, the New York Times, the code repositories, and the personal blogs of billions of Sarah Seabury Wards.

Yet, there are no helicopters. There are no federal indictments. Instead, there are keynote speeches and trillion-dollar valuations. The act that was a felony for Swartz is a business model for Altman. The difference is not the crime; the difference is that the new thieves are too big to raid. We have moved from a world where copyright was a weapon used against grandmothers to a world where it is a minor line item on a server bill. The "Pile" is a monument to the moment the law stopped pretending to be about justice and admitted it was only about power.

### **3.10 The Counter-Insurgency**

So, who is left to defend the system of knowledge? It is not the platform CEOs, who have traded verification for scale. And it is not the traditional institutions, many of whom are already signing licensing deals to sell the archives they were meant to protect.

The true defense is coming from a counter-insurgency of engineers and regulators who understand that the only way to stop a machine is to break its fuel supply.

First, there are the **Saboteurs**, led by researchers like Ben Zhao at the University of Chicago. Their project, **Nightshade**, offers a glimpse of the future of "Data Dignity." It is a tool that allows creators to invisibly "poison" their work before uploading it. If a model scrapes the data without consent, the poison corrupts the model's training weights. This is not a request for credit; it is a technological enforcement of boundaries. It asserts that if you steal the data, you inherit the poison.

Second, there are the **Verifiers**, organized under the **C2PA** (Coalition for Content Provenance and Authenticity). They are building the "Digital Nutrition Label" for the web—cryptographic metadata that locks the history of a file to its pixel. They are not trying to stop the flood of synthetic media; they are trying to ensure that human reality remains distinguishable from it.

### **3.11 The Ghost of Article 53**

By the spring of 2026, however, it became apparent that the regulatory counter-insurgency had stalled. While the EU AI Act remained on the books, the enforcement of **Article 53**—the requirement for detailed data transparency—had been hollowed out by a strategy of **"Malicious Compliance."**

The industry did not fight the law; they simply overwhelmed it. They deployed three specific tactics to ensure the "Black Box" remained sealed:

1. **The "Trade Secret" Defense:** When the EU AI Office demanded detailed summaries of training data, OpenAI and Google responded with documents so redacted they were functionally blank. They argued that revealing specific sources (e.g., "The New York Times") would violate trade secrets. They successfully lobbied regulators to accept "High-Level Summaries"—allowing them to claim they trained on "The Internet" rather than admitting to specific thefts.  
2. **The "Geofencing" Threat:** Meta (Facebook) escalated the conflict into a hostage crisis. Citing a "hostile regulatory environment," they withheld their multimodal **Llama 4** models from the European market entirely. It was a game of chicken: *Drop the transparency rules, or we turn off your future.*  
3. **The Stall:** In the summer of 2025, just before the Act's "legacy" deadline, the industry rushed to release every model in their pipeline. By flooding the market before August 2nd, they locked in a "grandfather clause" exemption that granted them two extra years of secrecy.

We must pause here to understand the magnitude of the choice we made. We did not just fail to enforce a rule; we rejected a future. Had Article 53 been enforced with forensic rigor, it would have introduced the **"Ingredient List"** to the information economy. In the twentieth century, we decided that corporations could not feed us physical food without listing the contents on the side of the box. We understood that a citizen cannot consent to consume what they cannot identify.

Instead, we chose the **Black Box**. We accepted the industry's lie that the "recipe" was a trade secret, rather than a public health hazard. In doing so, we sanctioned the creation of a synthetic consciousness that we are forbidden to audit. We chose to eat the mystery meat because it was cheap, and because we were told that asking for the ingredients would slow down the chef.

---

# **Master Index of Artifacts (Chapter 3\)**

| Artifact Name | Type | Section | Description |
| :---- | :---- | :---- | :---- |
| **The Skinner Box** | Concept | 3.1 | The "Behaviorist Delusion" (1957) that input/output frequency can replace the internal structure of mind. |
| **The Pseudo-Event** | Historical Concept | 3.2 | Daniel Boorstin's (1961) term for news manufactured solely to fill the distribution vacuum. |
| **Project Ocean** | Project | 3.3 | Google's mass scanning project (2004) that treated books as "tokens" rather than knowledge. |
| **Live Search Books** | Project | 3.3 | Microsoft's digitization project (ended 2008); the source of the "Clean Room" scanners. |
| **Destructive Digitization** | Method | 3.4 | The Haworth Press method of cutting spines to feed high-speed scanners. |
| **Project Panama** | Secret Project | 3.4 | Anthropic's (2026) initiative to "scan and destroy" books to exploit the "format shifting" loophole. |
| **The 26-Loan Cap** | Policy | 3.5 | HarperCollins' (2011) policy to make ebooks "expire" like paperbacks. |
| **The Zwicker Bill** | Legislation | 3.5 | The Feb 2026 New Jersey bill attempting to classify ebook restrictions as consumer fraud. |
| **The Hoboken Multiplier** | Statistic | 3.5 | Libraries pay 3-5x consumer price for expiring licenses [DiFilippo, D. (2026), "DiFilippo, D.", URL: https://newjerseymonitor.com/2026/02/22/libraries-pay-5-times-more-for-e-books-than-consumers-n-j-lawmakers-want-to-change-that/]. |
| **The OpenAI "Reset"** | Financial Data | 3.5 | OpenAI targeting $600B spend by 2030 vs. $13.1B revenue [Capoot, A., & Rooney, K. (2026), "Capoot, A., & Rooney, K.", URL: https://www.cnbc.com/2026/02/20/openai-resets-spending-expectations-600-billion-compute.html]. |
| **The Hoard** | Forensic Object | 3.6 | The sequestered property of the "Big Five" academic publishers; approx. 500B tokens. |
| **The 13T vs 190B Ledger** | Calculation | 3.6 | The math proving the "Public Web" (190B) is insufficient for "Frontier Models" (13T). |
| **Epistemic Nihilism** | Diagnosis | 3.8 | The state where a system prioritizes Frequency/Availability over Veracity/Safety. |
| **Nightshade** | Technical Tool | 3.10 | The "poison pill" for data sets; creates "Mutual Assured Destruction" for unauthorized scraping. |
| **Article 53** | Legislation | 3.11 | The "No Black Box" rule requiring detailed summaries of training data. |

---

---

## VERIFIED SILVER REFERENCE INDEX

1. [Helft, M. (2008), "Helft, M.", URL: https://www.nytimes.com/2008/05/24/technology/24soft.html]
2. [Reuters. (2024, March 29). Microsoft and OpenAI plotting $100 billion data center project 'Stargate'.]
3. [Niemeyer, Gerhart (1965), "The Image: A Guide to Pseudo-Events in America. By Daniel J. Boorstin. (New York and Boston: Harper Colophon Books, 1964. Pp. iv, 315. $1.75.)", American Political Science Review, Vol. 59, No. 1, pp. 149-149, DOI: 10.2307/1976138, URL: https://doi.org/10.2307/1976138]
4. [Dodge, Jesse; Sap, Maarten; Marasović, Ana; Agnew, William; Ilharco, Gabriel; Groeneveld, Dirk; Mitchell, Margaret; Gardner, Matt (2021), "Documenting Large Webtext Corpora: A Case Study on the Colossal Clean Crawled Corpus", Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing, pp. 1286-1305, DOI: 10.18653/v1/2021.emnlp-main.98, URL: https://doi.org/10.18653/v1/2021.emnlp-main.98]
5. [Mesarčík, Matúš; Solarova, Sara; Podroužek, Juraj; Bielikova, Maria (2022), "Stance on The Proposal for a Regulation Laying Down Harmonised Rules on Artificial Intelligence – Artificial Intelligence Act", Center for Open Science, DOI: 10.31235/osf.io/yzfg8, URL: https://doi.org/10.31235/osf.io/yzfg8]
6. [Page, Roderic (2009), "Google, Wikipedia, and EOL", Front Matter, DOI: 10.59350/x99bz-0af10, URL: https://doi.org/10.59350/x99bz-0af10]
7. [Gunasekar, S., et al. (2023). Textbooks Are All You Need. arXiv preprint arXiv:2306.11644.]
8. [IBM. (2013, October 18). IBM and MD Anderson Cancer Center to Fight Cancer. \[Press Release\].]
9. [Suber, Peter (2006), "Coming from Microsoft:  Windows Live Book Search", Front Matter, DOI: 10.63485/cew15-3p713, URL: https://doi.org/10.63485/cew15-3p713]
10. [Unknown Author (2018), "Watson Recommends Incorrect Cancer Treatments, System Training Questioned", Clinical OMICs, Vol. 5, No. 5, pp. 29-29, DOI: 10.1089/clinomi.05.05.17, URL: https://doi.org/10.1089/clinomi.05.05.17]
11. [Meyrick, Julian (2014), "A century after the torching of the Louvain library, what have we learned?", The Conversation, DOI: 10.64628/aa.43gsewjtk, URL: https://doi.org/10.64628/aa.43gsewjtk]
12. [Strickland, Eliza (2019), "IBM Watson, heal thyself: How IBM overpromised and underdelivered on AI health care", IEEE Spectrum, Vol. 56, No. 4, pp. 24-31, DOI: 10.1109/mspec.2019.8678513, URL: https://doi.org/10.1109/mspec.2019.8678513]
13. [Unknown Author (1871), "United States District Court, District of Rhode Island. Manchester et al. v. Hotchkiss", The American Law Register (1852-1891), Vol. 19, No. 6, pp. 379, DOI: 10.2307/3303631, URL: https://doi.org/10.2307/3303631]
14. [Unknown Author (2016), "Segan, LLC v. Zynga, Inc.
                    <i>Case No. 14-cv-01315-VC; 2015 U.S. Dist.. LEXIS 121545 (United States District Court for the Northern District of California, September 10, 2015)</i>", Gaming Law Review and Economics, Vol. 20, No. 1, pp. 98-103, DOI: 10.1089/glre.2016.20110, URL: https://doi.org/10.1089/glre.2016.20110]
15. [University of Texas System. (2016). Special Review of Procurement Procedures Related to the M.D. Anderson Cancer Center Oncology Expert Advisor Project.]
16. [Matulionyte, Rita (2023), "Researchers warn we could run out of data to train AI by 2026. What then?", The Conversation, DOI: 10.64628/aa.fr4tqjvvy, URL: https://doi.org/10.64628/aa.fr4tqjvvy]
17. [Washington Post. (2026, January 27). Inside 'Project Panama': Why Anthropic is destroying books to build a brain.]
18. [Reuters. (2024), "Reuters.", URL: https://www.reuters.com/technology/microsoft-openai-planning-100-billion-data-center-project-stargate-2024-03-29/]
19. [Cambridge Digital Library. (2011), "Cambridge Digital Library.", URL: https://cudl.lib.cam.ac.uk/collections/newton/1]
20. [Capoot, A., & Rooney, K. (2026), "Capoot, A., & Rooney, K.", URL: https://www.cnbc.com/2026/02/20/openai-resets-spending-expectations-600-billion-compute.html]
21. [DiFilippo, D. (2026), "DiFilippo, D.", URL: https://newjerseymonitor.com/2026/02/22/libraries-pay-5-times-more-for-e-books-than-consumers-n-j-lawmakers-want-to-change-that/]
22. [ReadersFirst. (2025), "ReadersFirst.", URL: https://www.readersfirst.org/news/publisher-price-watch-2025]
23. [Ocean County Library (2024), "Adopted 2024 Ocean County Library Report", URL: https://theoceancountylibrary.org/sites/default/files/about/report/2024-report.pdf]
24. [Niemeyer, Gerhart (1965), "The Image: A Guide to Pseudo-Events in America. By Daniel J. Boorstin. (New York and Boston: Harper Colophon Books, 1964. Pp. iv, 315. $1.75.)", American Political Science Review, Vol. 59, No. 1, pp. 149-149, DOI: 10.2307/1976138, URL: https://doi.org/10.2307/1976138]
25. [Hack-Polay, Dieu (2011), "Digital Library", Digitisation Perspectives, pp. 167-177, DOI: 10.1007/978-94-6091-299-3_10, URL: https://doi.org/10.1007/978-94-6091-299-3_10]
26. [Capoot, A., & Rooney, K. (2026, February 20). OpenAI resets spending expectations, tells investors compute target is around $600 billion by 2030. CNBC.]
27. [DiFilippo, D. (2026, February 22). Libraries pay 5 times more for e-books than consumers. N.J. lawmakers want to change that. New Jersey Monitor/PhillyVoice.]
28. [Dodge, Jesse; Sap, Maarten; Marasović, Ana; Agnew, William; Ilharco, Gabriel; Groeneveld, Dirk; Mitchell, Margaret; Gardner, Matt (2021), "Documenting Large Webtext Corpora: A Case Study on the Colossal Clean Crawled Corpus", Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing, pp. 1286-1305, DOI: 10.18653/v1/2021.emnlp-main.98, URL: https://doi.org/10.18653/v1/2021.emnlp-main.98]
29. [Mesarčík, Matúš; Solarova, Sara; Podroužek, Juraj; Bielikova, Maria (2022), "Stance on The Proposal for a Regulation Laying Down Harmonised Rules on Artificial Intelligence – Artificial Intelligence Act", Center for Open Science, DOI: 10.31235/osf.io/yzfg8, URL: https://doi.org/10.31235/osf.io/yzfg8]
30. [Page, Roderic (2009), "Google, Wikipedia, and EOL", Front Matter, DOI: 10.59350/x99bz-0af10, URL: https://doi.org/10.59350/x99bz-0af10]
31. [Gunasekar, S., et al. (2023). Textbooks Are All You Need. arXiv preprint arXiv:2306.11644.]
32. [Unknown Author (2000), "New York Times Millennium/Microsoft Poll, July 1999", ICPSR Data Holdings, DOI: 10.3886/icpsr02848, URL: https://doi.org/10.3886/icpsr02848]
33. [IBM. (2013, October 18). IBM and MD Anderson Cancer Center to Fight Cancer. \[Press Release\].]
34. [Suber, Peter (2006), "Coming from Microsoft:  Windows Live Book Search", Front Matter, DOI: 10.63485/cew15-3p713, URL: https://doi.org/10.63485/cew15-3p713]
35. [Waznis, Betty (2024), "Materials Budget Allocation Methods at San Diego County Library", Public Library Collection Development in the Information Age, pp. 25-32, DOI: 10.1201/9781003573074-4, URL: https://doi.org/10.1201/9781003573074-4]
36. [ReadersFirst. (2025). Publisher Price Watch: 2025 Summary.]
37. [Unknown Author (2018), "Watson Recommends Incorrect Cancer Treatments, System Training Questioned", Clinical OMICs, Vol. 5, No. 5, pp. 29-29, DOI: 10.1089/clinomi.05.05.17, URL: https://doi.org/10.1089/clinomi.05.05.17]
38. [Meyrick, Julian (2014), "A century after the torching of the Louvain library, what have we learned?", The Conversation, DOI: 10.64628/aa.43gsewjtk, URL: https://doi.org/10.64628/aa.43gsewjtk]
39. [Strickland, Eliza (2019), "IBM Watson, heal thyself: How IBM overpromised and underdelivered on AI health care", IEEE Spectrum, Vol. 56, No. 4, pp. 24-31, DOI: 10.1109/mspec.2019.8678513, URL: https://doi.org/10.1109/mspec.2019.8678513]
40. [Unknown Author (1871), "United States District Court, District of Rhode Island. Manchester et al. v. Hotchkiss", The American Law Register (1852-1891), Vol. 19, No. 6, pp. 379, DOI: 10.2307/3303631, URL: https://doi.org/10.2307/3303631]
41. [Unknown Author (2016), "Segan, LLC v. Zynga, Inc.
                    <i>Case No. 14-cv-01315-VC; 2015 U.S. Dist.. LEXIS 121545 (United States District Court for the Northern District of California, September 10, 2015)</i>", Gaming Law Review and Economics, Vol. 20, No. 1, pp. 98-103, DOI: 10.1089/glre.2016.20110, URL: https://doi.org/10.1089/glre.2016.20110]
42. [University of Texas System. (2016). Special Review of Procurement Procedures Related to the M.D. Anderson Cancer Center Oncology Expert Advisor Project.]
43. [Matulionyte, Rita (2023), "Researchers warn we could run out of data to train AI by 2026. What then?", The Conversation, DOI: 10.64628/aa.fr4tqjvvy, URL: https://doi.org/10.64628/aa.fr4tqjvvy]
44. [Washington Post. (2026, January 27). Inside 'Project Panama': Why Anthropic is destroying books to build a brain.]
45. [Niemeyer, Gerhart (1965), "The Image: A Guide to Pseudo-Events in America. By Daniel J. Boorstin. (New York and Boston: Harper Colophon Books, 1964. Pp. iv, 315. $1.75.)", American Political Science Review, Vol. 59, No. 1, pp. 149-149, DOI: 10.2307/1976138, URL: https://doi.org/10.2307/1976138]
46. [Hack-Polay, Dieu (2011), "Digital Library", Digitisation Perspectives, pp. 167-177, DOI: 10.1007/978-94-6091-299-3_10, URL: https://doi.org/10.1007/978-94-6091-299-3_10]
47. [Capoot, A., & Rooney, K. (2026, February 20). OpenAI resets spending expectations, tells investors compute target is around $600 billion by 2030. CNBC.]
48. [DiFilippo, D. (2026, February 22). Libraries pay 5 times more for e-books than consumers. N.J. lawmakers want to change that. New Jersey Monitor/PhillyVoice.]
49. [Dodge, Jesse; Sap, Maarten; Marasović, Ana; Agnew, William; Ilharco, Gabriel; Groeneveld, Dirk; Mitchell, Margaret; Gardner, Matt (2021), "Documenting Large Webtext Corpora: A Case Study on the Colossal Clean Crawled Corpus", Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing, pp. 1286-1305, DOI: 10.18653/v1/2021.emnlp-main.98, URL: https://doi.org/10.18653/v1/2021.emnlp-main.98]
50. [Mesarčík, Matúš; Solarova, Sara; Podroužek, Juraj; Bielikova, Maria (2022), "Stance on The Proposal for a Regulation Laying Down Harmonised Rules on Artificial Intelligence – Artificial Intelligence Act", Center for Open Science, DOI: 10.31235/osf.io/yzfg8, URL: https://doi.org/10.31235/osf.io/yzfg8]
51. [Page, Roderic (2009), "Google, Wikipedia, and EOL", Front Matter, DOI: 10.59350/x99bz-0af10, URL: https://doi.org/10.59350/x99bz-0af10]
52. [Gunasekar, S., et al. (2023). Textbooks Are All You Need. arXiv preprint arXiv:2306.11644.]
53. [Unknown Author (2000), "New York Times Millennium/Microsoft Poll, July 1999", ICPSR Data Holdings, DOI: 10.3886/icpsr02848, URL: https://doi.org/10.3886/icpsr02848]
54. [IBM. (2013, October 18). IBM and MD Anderson Cancer Center to Fight Cancer. \[Press Release\].]
55. [Suber, Peter (2006), "Coming from Microsoft:  Windows Live Book Search", Front Matter, DOI: 10.63485/cew15-3p713, URL: https://doi.org/10.63485/cew15-3p713]
56. [Waznis, Betty (2024), "Materials Budget Allocation Methods at San Diego County Library", Public Library Collection Development in the Information Age, pp. 25-32, DOI: 10.1201/9781003573074-4, URL: https://doi.org/10.1201/9781003573074-4]
57. [ReadersFirst. (2025). Publisher Price Watch: 2025 Summary.]
58. [Reuters. (2024, March 29). Microsoft and OpenAI plotting $100 billion data center project 'Stargate'.]
59. [Unknown Author (2018), "Watson Recommends Incorrect Cancer Treatments, System Training Questioned", Clinical OMICs, Vol. 5, No. 5, pp. 29-29, DOI: 10.1089/clinomi.05.05.17, URL: https://doi.org/10.1089/clinomi.05.05.17]
60. [Meyrick, Julian (2014), "A century after the torching of the Louvain library, what have we learned?", The Conversation, DOI: 10.64628/aa.43gsewjtk, URL: https://doi.org/10.64628/aa.43gsewjtk]
61. [Strickland, Eliza (2019), "IBM Watson, heal thyself: How IBM overpromised and underdelivered on AI health care", IEEE Spectrum, Vol. 56, No. 4, pp. 24-31, DOI: 10.1109/mspec.2019.8678513, URL: https://doi.org/10.1109/mspec.2019.8678513]
62. [Unknown Author (1871), "United States District Court, District of Rhode Island. Manchester et al. v. Hotchkiss", The American Law Register (1852-1891), Vol. 19, No. 6, pp. 379, DOI: 10.2307/3303631, URL: https://doi.org/10.2307/3303631]
63. [Unknown Author (2016), "Segan, LLC v. Zynga, Inc.
                    <i>Case No. 14-cv-01315-VC; 2015 U.S. Dist.. LEXIS 121545 (United States District Court for the Northern District of California, September 10, 2015)</i>", Gaming Law Review and Economics, Vol. 20, No. 1, pp. 98-103, DOI: 10.1089/glre.2016.20110, URL: https://doi.org/10.1089/glre.2016.20110]
64. [University of Texas System. (2016). Special Review of Procurement Procedures Related to the M.D. Anderson Cancer Center Oncology Expert Advisor Project.]
65. [Matulionyte, Rita (2023), "Researchers warn we could run out of data to train AI by 2026. What then?", The Conversation, DOI: 10.64628/aa.fr4tqjvvy, URL: https://doi.org/10.64628/aa.fr4tqjvvy]
66. [Washington Post. (2026, January 27). Inside 'Project Panama': Why Anthropic is destroying books to build a brain.]
