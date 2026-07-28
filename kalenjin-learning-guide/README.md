# Kalenjin Learning Guide

A colourful, fillable 12-week teacher workspace adapted from the
`Kalenjin_12_Week_Teacher_Guide_Translation_Template.docx` source document.

## What it includes

- All 12 weeks of objectives, vocabulary, sentence targets, dialogues, lesson
  flow, midweek practice, and homework.
- Auto-saving Kalenjin translation and teacher-note fields.
- Activity checklists and live course progress.
- Guide-wide search, assessment checkpoints, translator notes, printing, and
  JSON backup/restore.
- Responsive layouts for desktop, tablet, and phone.

Entries are stored in the current browser with `localStorage`. Use **Back up**
to download a portable JSON copy before moving to another device or clearing
browser data.

## Preview

Run any static file server from this directory, for example:

```powershell
python -m http.server 4173
```

Then open `http://localhost:4173`.

## Firebase Hosting

The default Firebase project is `kalenjin-learning-guide`. Deploy from this
directory with:

```powershell
firebase deploy --only hosting
```
