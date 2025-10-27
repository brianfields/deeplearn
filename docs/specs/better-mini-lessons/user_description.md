# Better Mini-Lessons: User Description

## Current Structure
A unit consists of:
- A podcast for the unit (covers entire unit content)
- A series of lessons, where each lesson contains:
  - A "mini-lesson" (text/content)
  - A series of exercises (currently all MCQs, will expand in future)

## Desired Structure
A unit consists of:
- An **intro podcast** (teases what the unit will be about, engages and hooks the learner)
- A series of lessons, where each lesson contains:
  - A **lesson-level podcast** (covers the lesson material in a narrative, engaging fashion)
  - A "mini-lesson" (text/content)
  - A series of exercises

## Key Changes
1. **Unit podcast focus shift**: From covering entire unit content → teasing/hooking learners about what's to come
2. **New lesson-level podcasts**: Each lesson gets its own podcast that covers the same material as the mini-lesson but in a more narrative and engaging way (not just reading the mini-lesson)

## Requirements/Stipulations
1. **Intro line**: Each podcast should start with an intro line, e.g., "Lesson 2. How to temper chocolate."
2. **Navigation**: In the podcast playing UI, users should be able to skip ahead or back to podcasts of other lessons (and the intro)
3. **Autoplay option**: There should be an option (on by default) to autoplay, meaning the app will move from one lesson podcast to the next within a unit until all unit podcasts are exhausted
4. **Content quality**: The podcast for a lesson should cover the same material as the mini-lesson but in a more narrative and engaging fashion—it shouldn't just read the mini-lesson

## Implications
- Content creation workflow changes (generating intro podcasts + lesson podcasts)
- Lesson delivery changes (podcast playback UI, navigation, autoplay)
- Data model changes (storing multiple podcasts per unit: 1 intro + N lesson podcasts)

## Design Decisions (from clarifying questions)

1. **Generation Timing**: All podcasts (intro + lesson podcasts) generated upfront during unit creation
2. **Intro Podcast Content**: Generated from mini-lessons with a prompt emphasizing hooks that make material interesting and important feeling. Target: ~500 words max.
3. **Navigation & Autoplay**: 
   - Player has skip forward/backward buttons to move between podcasts
   - Autoplay is linear: intro → lesson 1 → lesson 2 → ... → lesson N
4. **Lesson Flow**: User can play lesson podcast when on that lesson's screen. Podcast player always visible.
5. **Offline Support**: Download all podcasts during unit sync
6. **Migration**: NO backward compatibility needed. Database will be wiped. No existing users.
7. **Admin Interface**: Read-only. Shows links to each podcast with associated lesson.
8. **Intro Lines**: 
   - Intro podcast: No specific intro line, just starts with engaging teaser
   - Lesson podcasts: Include intro line in transcript, e.g., "Lesson 2. How to temper chocolate."
9. **Storage**: Add podcast fields to `LessonModel` (each lesson owns its podcast)
10. **Validation**: All podcasts must be generated before unit marked as "completed"
