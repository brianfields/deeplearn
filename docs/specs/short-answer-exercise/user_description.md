# Short Answer Exercise - User Description

At present, we only have multiple choice question exercise types in a lesson. I'd like to add short answer as a 2nd exercise type. Some details:

1. The system will generate short answer alongside the multiple choice questions for a lesson. Eventually, we'll have the learning_coach decide on the mix of questions, but let's just do 5 of each for now.

2. When the short answer question is created by the backend, I'd like it to provide as many correct answers as makes sense to judge correct; that should improve the checking of whether the provided answer is correct.

3. The system should target 1-3 word answers. We don't want the learner to have to type much on a mobile device and we want to maximize the likelihood of being able to accurately determine whether the provided answer is correct. So, the best types of questions lead to a specific one word answer.

4. We should follow best practices as outlined by pedagogical literature for these types of questions to best test learning of the material.

5. We should provide common misconceptions for these questions and LO mappings, just like we do for multiple choice questions. We should provide explanations for why commonly provided wrong answers are wrong. We should also provide a reasoning for why the correct answer is correct.

6. The front-end mobile app will ask the MCQ questions first followed by the short answer for a lesson.

7. The learner will answer by typing on the keyboard.

8. Eventually, we'll support near match results via embedding lookup, but let's not worry about that for now.

9. Short answer questions should work offline, just like MCQ does today.

10. The admin interface will show short answer questions as part of a lesson just like it does for MCQ today.
