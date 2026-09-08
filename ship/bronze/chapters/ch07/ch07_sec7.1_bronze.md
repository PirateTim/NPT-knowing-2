# Chapter 7: History Is Shrinking

> "You own nothing. You are licensing a temporary visual experience."
> — **Ubisoft Customer Support**, responding to the deletion of *The Crew* (2024)

> "The web is not a library. It is a commercial real estate project where the rent is due every month."
> — **Pew Research Center**, *Digital Decay* (2024)

### 7.1 The Handshake: The Webmaster's Witness (1998)

The "Gentleman’s Agreement" that held the internet together for thirty years was not a treaty signed in Geneva. It was a text file named `robots.txt`, and I remember exactly how fragile it felt when I first typed it.

In 1998, I was working as the webmaster for **Lippincott Williams & Wilkins (LWW)**, a division of Wolters Kluwer. My job was not to keep the web open; my job was to close it. I was tasked with building the company’s **first pay-per-article system**. We were erecting the high walls that would eventually lock up the world’s scientific knowledge, actively separating "Verified Knowledge" (The Hoard) from the chaos of the open internet.

But while I was hard-coding credit card gateways to keep humans out, I was simultaneously hand-editing a simple text file to let the machines in.

I remember staring at the command line, editing the file that controlled the behavior of the early web crawlers. The syntax was almost comically simple:

```text
User-agent: *
Disallow: /private/
```

I looked at it and thought: *Wait. This isn't a lock. This is a polite request.*

The irony was stark. I was spending thousands of dollars and man-hours on encryption and authentication to ensure that no human could read a PDF without paying $35. Yet, to stop a bot from taking the entire library, all I had was this text file. Technically, `robots.txt` does absolutely nothing to stop a crawler. It relies entirely on the honor of the visitor.

In 1998, that was enough. The crawlers from AltaVista, Yahoo, and the nascent Google respected the signage. We struck a delicate bargain: we allowed Google Scholar to peek over the wall to index our metadata (facilitating discovery/SEO), provided they didn't steal the asset. It was a handshake. They got the traffic; we kept the ownership.

But handshakes only work between people who have shame.
