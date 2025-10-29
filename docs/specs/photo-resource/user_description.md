# Photo Resource Feature - User Description

## Problem Statement
There is a placeholder for "Take a photo" in the mobile app's AddResourceScreen that needs to be implemented. Additionally, we need to add a "Choose a photo" option to select photos from the device's photo library.

## Technical Approach
Photos need to be interpreted to extract text that can be used in the learning_coach conversation (similar to the resource-upload feature). The extraction process should:
1. Send the photo to OpenAI (through the llm_services module)
2. Request a detailed description of the image plus any visible text
3. Use the combined description and text as the extracted text for the resource

## User Capabilities
- Take a photo using the device camera
- Choose a photo from the device's photo library
- Have the photo automatically processed to extract meaningful text for learning coach conversations

## Reference
See docs/specs/resource-upload/spec.md for the high-level description of the related resource upload feature.
