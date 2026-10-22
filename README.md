PressDesk

PressDesk is a web app for editors at small independent presses who receive manuscripts from writers. Instead of keeping submissions scattered across email attachments, an editor uploads each manuscript as a Word, PDF, or text file, and PressDesk automatically splits it into chapters. They can then read it chapter by chapter, track which chapters they’ve read, add notes as they go, and move the manuscript through the decision stages: received, reading, shortlisted, accepted, or declined. Each press’s manuscripts are private to its own account.

Live site: [link to deployed app]

Show Image

Contents
Rationale
User stories
UX design
Features
Data schema
Security
Technologies
Testing
Deployment
Running locally
Development notes
Credits
Rationale

<!-- Why does this app need to exist? Write this in your own voice. Cover: - the problem small presses have with incoming manuscripts - who the target audience is (small indie presses, editors, readers) - why a web app is the right solution - the value it gives them -->
Target audience
[e.g. editors at small independent presses who receive manuscripts by email]
The problem

[Describe the problem.]

Why a web app

[Explain.]

User stories
<!-- Write these from the publisher's point of view. The final app should match them. -->
As a…	I want to…	So that…
publisher	upload a manuscript in .docx, .txt or .pdf	I can read submissions in one place
publisher	see the manuscript split into chapters	I can read it a chapter at a time
publisher	add, edit and delete notes on a chapter	I can record my thoughts as I read
publisher	set a status (received, reading, shortlisted, accepted, declined)	I can track where each submission is
publisher	filter and search my manuscripts	I can find a submission quickly
publisher	know my manuscripts are private to my account	other presses can't see them
[add your own]		
UX design
<!-- Include your wireframes or mockups. Save images in docs/ and link them here. -->
Wireframes

Show Image

Colour scheme
<!-- List the main colours from style.css and why you chose them. -->
Colour	Hex	Used for
Teal	
#0d6b5a	Header, main buttons
Yellow	
#ffd84d	Highlights, focus outlines
[add more]		
Typography
Bricolage Grotesque for headings. [Why you chose it.]
Atkinson Hyperlegible for body text, designed by the Braille Institute to be easy to read for people with low vision.
Accessibility
<!-- What you did and why. -->
[e.g. visible focus outlines for keyboard users]
[e.g. labels on every form field]
[e.g. colour contrast checked]
Design decisions
<!-- Explain any choices that go against usual conventions, for example: opening a "received" manuscript automatically marks it as "reading"; keeping all routes inside create_app(). -->
Features
<!-- One short section per feature, each with a screenshot. -->
Register and log in

[Description] Show Image

Dashboard

[Status counts, filter, search.]

Upload a manuscript

[Drag and drop, progress bar, works without JavaScript, file checks.]

Read by chapter

[Chapter list, previous/next, mark as read.]

Notes

[Add, edit, delete.]

Status changes

[How status works.]

Edit and delete manuscripts

[Including the confirmation page.]

Error pages

[Custom 404 and 500 pages.]

Future features
[Ideas you didn't have time for.]
Data schema
<!-- Check field names against app/models.py. A diagram image is good too. -->

Show Image

User: a publisher account

Field	Type	Notes
id	Integer	Primary key
name	String	
email	String	Unique, stored in lower case
press_name	String	
password_hash	String	Never stores the plain password

Manuscript: one submission, owned by one user

Field	Type	Notes
id	Integer	Primary key
title	String	
author_name	String	
genre	String	
status	String	received / reading / shortlisted / accepted / declined
uploaded_at	DateTime	
owner_id	Integer	Foreign key → User

Chapter: one chapter of a manuscript

Field	Type	Notes
id	Integer	Primary key
number	Integer	Order in the manuscript
title	String	
content	Text	
is_read	Boolean	
manuscript_id	Integer	Foreign key → Manuscript

Note: a note on one chapter

Field	Type	Notes
id	Integer	Primary key
body	Text	
created_at	DateTime	
updated_at	DateTime	Empty until edited
chapter_id	Integer	Foreign key → Chapter

Relationships: one user has many manuscripts; one manuscript has many chapters; one chapter has many notes. Deleting a manuscript deletes its chapters and notes.

Security
Secret keys and the database URL are kept in environment variables (env.py locally, which is in .gitignore; Config Vars on Heroku). They are never committed.
DEBUG is off unless explicitly set to "True", and is off on the live site.
Passwords are hashed, never stored as plain text.
All manuscript, chapter and note pages require login.
Every item is checked against the logged-in publisher, and other publishers' items return a 404.
All forms are protected against CSRF.
Redirects after login only go to pages on this site.
Uploads are limited to 5 MB and to .docx, .txt and .pdf files.
Technologies
Languages: Python, HTML, CSS, JavaScript
Framework and libraries: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, python-docx, pypdf, Gunicorn
Database: SQLite locally, PostgreSQL on Heroku
Tools: Git, GitHub, VS Code, Heroku, pytest
[Add any design tools you used, e.g. for wireframes]
Testing
Automated tests

Run with:

bash
python -m pytest

[Say what the tests cover and add a screenshot of them passing.]

Manual testing
<!-- Do these on the live site in a private window. Fill in the Result column honestly. -->
Test	Steps	Expected	Result
Register	Fill in the form with new details	Account created, message shown	
Duplicate email	Register with an existing email	Error message	
Log in / out			
Upload .txt	Upload samples/frankenstein.txt	[n] chapters	
Upload .docx	Upload samples/alice-in-wonderland.docx	[n] chapters	
Upload .pdf	Upload samples/alice-in-wonderland.pdf	[n] chapters	
No headings	Upload samples/im-bernsteinwald.txt	1 chapter, "Full manuscript"	
Empty file	Upload samples/empty.txt	Error: "The file you chose is empty."	
Wrong file type	Upload a .png	Error message	
Add / edit / delete note			
Change status			
Edit manuscript details			
Delete manuscript		Confirmation page, then deleted	
Another publisher's data	Visit another account's manuscript URL	404 page	
Page that doesn't exist	Visit /manuscripts/9999	404 page	
Back button	Use back after deleting	Nothing breaks	
Mobile layout	Open on a phone	Layout fits the screen	
Validators
Check	Tool	Result
HTML	W3C Markup Validator	
CSS	W3C CSS Validator (Jigsaw)	
JavaScript	JSHint	
Python	flake8 (PEP8)	
Accessibility	[e.g. Lighthouse or WAVE]	
Bugs

Fixed

Bug	Fix
[e.g. syntax error in demo data]	[what you changed]

Known and unfixed

Bug	Why it's left
A short line starting "Chapter 3 had been…" in the middle of a chapter would be treated as a heading	[your explanation]
Contents lists at the start of a book create near-empty chapters	[your explanation]
Deployment
<!-- Write these steps as you actually do them, so they're accurate. -->
Heroku
Create a new app on Heroku.
Add the Heroku Postgres add-on.
In Settings → Config Vars, add:
SECRET_KEY: a new random value
DEBUG: False
(DATABASE_URL is added automatically by Postgres.)
In Deploy, connect the GitHub repository and deploy the main branch.
Run the database migrations: [how you did it, e.g. the release line in the Procfile]
Optionally add demo data: heroku run python seed.py
[Check the live site matches the local version.]
Demo account

The demo account contains sample data only:

Email: demo@pressdesk.example.com
Password: DemoPress2026!
Running locally
bash
git clone https://github.com/zsheerani1/PressDesk.git
cd PressDesk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Copy env_example.py to a new file called env.py and fill in your own values.
Set up the database: flask --app run db upgrade
Optionally add demo data: python seed.py
Start the app: python run.py
Development notes
<!-- Be accurate about how the project was developed. -->

[e.g. PressDesk was developed locally before version control was set up and moved into this repository on 22 October 2026. Changes since then are committed individually.]

Credits
Code
[Any tutorials, documentation or code examples you used, with links]
[How you used AI tools, if your course asks you to declare it]
Content
Frankenstein by Mary Shelley, Alice's Adventures in Wonderland by Lewis Carroll and Im Bernsteinwald by Wilhelm Bölsche: public domain, from Project Gutenberg.
Demo manuscripts in seed.py use short extracts from public-domain novels by Jane Austen, Charles Dickens and Herman Melville.
Fonts
Bricolage Grotesque and Atkinson Hyperlegible from Google Fonts.
