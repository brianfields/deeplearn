# Content From Nothing - User Description

This will be a purely backend feature for generating content. As you can see from `backend/modules/content_creator/`, new content is generated for a lesson from some source material through a "flow_engine" flow. There is also a helper script called `backend/scripts/create_unit.py` for creating content. I'd like to improve this flow in a couple of ways. 

(1) I want to be able to specify a topic for a unit (without providing source material) and have the flow generate the appropriate number of lessons for that unit, with the understanding that each lesson should be about 5 minutes of work for the student. A lesson consists of a didactic snippet followed by some MCQs (~5). I believe the simplest way to do that would be to have the system generate some source material for the unit that is cohesive and then use that as source material in a flow not to dissimilar to the one that exists. I'd like to be able to retain the ability to run a flow with source material. 

A material change is to create multiple lessons for a unit. Let's assume when a user specifies a unit they are thinking of no more than an hour of material (e.g. no more than 20 lessons), but it could be fewer if fewer are sufficient. 

So, in summary, upon completion of this project, it should be possible to invoke the flow in content_creator to create multiple lessons for a unit, either by providing source material or having the system construct the source material itself. I don't need to retain the ability to create individual lessons.