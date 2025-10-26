# Refine LOs - User Description

## Overview
Refine how Learning Objectives (LOs) are used throughout the application.

## Requested Changes

### 1. Fix Results Screen Bug
There is a bug in the results screen after a lesson where, if you run a lesson more than once, it will happily say that you've--for instance--got 9/5 correct. It should never be that you've gotten more exercises correct than exist. Instead, it should judge whether you got the question right the last time you were asked the question.

### 2. Remove Summary Box
The summary box at the top of the result page is not really helpful; let's get rid of that.

### 3. Add Short Titles to LOs
When LOs are created (originally as part of the learning_coach conversation but then later during unit creation), let's give the LOs short titles as well as longer descriptions. That way, in these tables we can show the short titles.

### 4. Remove Uncovered LOs from Units
We shouldn't list LOs as part of a unit if they aren't covered by that unit. I think that can happen if the LO is established but then there aren't enough lessons to cover all the LOs. In that case, we should eliminate the LO from the unit. Ideally, the learning_coach would realize this so that, for instance, if the learner requests fewer lessons, the LOs adjust.

### 5. Show Only Lesson LOs on Results Screen
On the results screen, I'd like to just list progress on the learning objectives that appeared in the lesson; the full unit LOs progress should appear on the unit detail page.
