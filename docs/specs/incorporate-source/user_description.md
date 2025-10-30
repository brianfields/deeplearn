# Incorporate Source - User Description

## Problem Statement

In the content_creator module, we have a flow that creates unit content. The first step is to create source material. We need to do that if we aren't provided source material. 

However, during the conversation with the learning_coach, the learner can share resource(s) that have content. If the learner does choose to share resources, we should use the extracted text from those resources as the source material, as opposed to generating our own.

## Core Requirement

When creating unit content, if the learner has shared resources during their learning_coach conversation, use the extracted text from those resources as source material instead of generating new source material.
