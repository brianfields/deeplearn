# Resource Upload - User Description

## Working Name
Resource Upload

## Clarifications (from discussion)

1. **Scope**: Step one of resource handling. Future: use during unit creation, reuse across conversations
2. **File types**: PDF, DOCX, PPTX, TXT, MD. Preserve some structure in extracted text. YouTube: use YouTube transcript. Web: main article content only
3. **Storage**: Permanent S3 storage + database table. Users can see/reuse resources. No deletion for v1
4. **Coach integration**: Immediate acknowledgment. Optional upload button on initial screen. Link resources to created units
5. **Content creator**: Will eventually access resources, but not in this phase
6. **UI priority**: Mobile-only uploads. Admin is read-only (show resources per unit, per user)
7. **URL validation**: Basic validation. Error reporting. Direct PDF/PPTX links can be placeholder
8. **Size limits**: 100MB file size, 100KB extracted text. Large PDFs: limit to 5 pages, ask user which pages
9. **Data model**: New `resource` module with table. FKs to `object_store` for uploaded files
10. **Testing**: Out of scope for v1

**Architecture note**: This is v1. Architecture should be complete, but some extraction methods can be placeholders for future implementation.

## What it is

When you're talking to the learning coach and building a new unit, you can hand it the source material you want it to learn from. You can do that in two ways:

1. Upload a file
2. Paste a link

There's a little "+" next to the message box (like ChatGPT has). Tap that and you get a panel where you can either drag in a file or give us a URL.

## What we accept

**Files**: docs, PDFs, PowerPoints, text, etc.

**Links**: normal web pages, direct links to PDFs / decks, YouTube videos.

- If you give us a YouTube link, we'll pull the transcript.
- If you give us a normal URL, we'll scrape the page.
- If you upload a file, we'll read it.

## What happens after you add something

As soon as you upload/paste, we immediately grab the content behind it and start using it in the conversation. The coach can now say things like "Based on slide 7 in your deck…" or "Here's a lesson pulled from this article…" — so it feels like you're co-writing the unit together using your own material.

In other words: you don't have to manually summarize your source. You just hand it over, and it becomes part of the working context for building the unit.

## What we store

We also save what you gave us, so we can reuse it later:

**For uploaded files:**
- We store the raw file in object storage (S3).
- We create a database row pointing to that file.

**For links:**
- We create a database row with the URL.

**For everything:**
- We store the extracted text / transcript / scraped content alongside the resource in the database.

So each resource ends up having:
- where it came from (file vs URL),
- how to fetch the original (S3 link or URL),
- and the cleaned/parsed text we pulled out.

That means later on we can trace any lesson back to the original source, and we don't have to re-scrape or re-parse the same thing over and over.
