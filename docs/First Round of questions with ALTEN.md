	
manual steps -> there is no documentation (fictional use case); currently engineer looks at the configuration and validates if what he sees is what is expected. No example animations (free to choose from a "pool (he named as examples)" e.g. navigation etc. -- field of use for animation: industire based would be vavourable but not neccessary) - e.g. a game would be fine as well 

(The test is for the display itself so what is displayed is not neccessary)

what is to be detected: Design misstakes, flicering, missing parts, what is displayed is generally wrong - in industrie topics: In a menu there is a delay for e.g a pop-up, focus function is wrong (highlighting for a set time-frame).

Are there any software quality metrics (documented)? - looking for a MVP so no test coverage etc. more interested in the process and the presentation - but SOPRA-Team will take a look quality (pull-requests etc.) Also view SOPRA requirement - sheet (API-Test is required "Lucas").

Constraints - tech-stack: deployment via dockploy (accessable through a browser) - no others 

The User is a Engineer - the software should focus on evaluating the different models 

-> Frontend user uploads a clip chooses a model and some other parameters (optional) - executes and evaluates against the metrics - also other things like highliting the misshaps or differences, results etc the user can see it afterwards - can be evaluation of the modles and/or evaluation of the detection of issues (focus may be one or the other or both)

Models are provided alongside api keys - multiple models are still in the making 

The model can be fixed but choosing free is also an option but not an requirement (good practice) - not bound to the model - keep resource usage in mind and adapt (maybe lightweight models)

the group can choose how the frontend looks - does not have to look the most fancy but more interested in the backend and the result of the evaluation but almost all of the non functional requirements are up to us. There only needs to be an interaction/evaluation possible. 

Add metrics along side the MVP Requirements plan (Staffelung)

input 10ct output 1 dollar both per 1Mio tokens For the GPT Modell 
ALTEN is more interested in number of tokens 

pre processing if done well and also ***well documented*** (when and why)is encouraged to safe on cost and tokens (e.g breaking down a 60fps video) also may be 

the main part is the process and the decicions made (explain them and defend them)

there always should be a preprocessing of the video (format, scaling, filters, background noice)

the issues flagged in the process do not have to be fixed - only inform and provide information 

the two models benchmarked against each other do not have to be configured the same way they can be optimized but has to be documented and defendable 

-> For us first focus on the eval of metrics then if there is time the eval of issues and presenting them to the user




 



