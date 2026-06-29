# Presenter Script

## Slide 1: Title

**What I should say:** I introduce the project as a Battery Re-X digital twin for automated lifecycle decision support.

**Key technical point:** The system is not only a visual Unity demo; it is connected to backend AI and ML components.

**Possible question:** Is this only a simulation?

**Best answer:** It is a working software proof-of-concept. The Unity environment is simulated, while the backend classifiers, SOH model, API routes, and model artifacts are implemented.

## Slide 2: Problem & Motivation

**What I should say:** I explain why automated battery sorting matters: it reduces manual uncertainty and supports circular battery flows.

**Key technical point:** The key challenge is separating visual classification from health assessment.

**Possible question:** Why is manual sorting not enough?

**Best answer:** Manual sorting can identify visible shape and damage, but it cannot reliably estimate SOH or electrical risk without sensor or BMS data.

## Slide 3: Project Vision

**What I should say:** I describe the full pipeline from intake to robotic sorting.

**Key technical point:** The architecture separates perception, health prediction, and lifecycle decision logic.

**Possible question:** Why split vision and SOH?

**Best answer:** Because the image can identify the battery form factor but cannot measure cycle aging, resistance, voltage, or temperature.

## Slide 4: Dataset 1: RecyBat24

**What I should say:** I explain the visual dataset used for battery shape classification.

**Key technical point:** The classifier uses image pixels and compares methods on a balanced 90-image subset.

**Possible question:** Did the classifier learn from the filename?

**Best answer:** No. Folder names are used as ground-truth labels during training and evaluation, but runtime prediction extracts image features from pixels.

## Slide 5: Dataset 2: Battery Aging Data

**What I should say:** I describe the NASA aging table used for SOH regression.

**Key technical point:** SOH is derived from capacity, while inference uses measurable health parameters.

**Possible question:** Why not train only from images?

**Best answer:** Images do not contain cycle count, internal resistance, capacity fade, or voltage behavior, so SOH needs health data.

## Slide 6: Why Image Alone Is Not Enough

**What I should say:** I clarify that the system does not infer SOH from an image.

**Key technical point:** SOH requires health parameters; the image only supplies the battery type.

**Possible question:** Can a neural network estimate SOH from a photo?

**Best answer:** A photo may show damage, but it cannot reliably infer capacity fade or resistance. For this project I use sensor-style health inputs for SOH.

## Slide 7: System Architecture

**What I should say:** I explain how the Unity simulation communicates with backend AI and ML services.

**Key technical point:** The architecture is modular: vision, SOH, decision, and sorting are separate components.

**Possible question:** Where is the backend decision made?

**Best answer:** The backend exposes /predict-soh for ML-based SOH and Re-X routing; Unity calls it after mock sensor readings are generated.

## Slide 8: AI Vision Pipeline

**What I should say:** I describe the visual classifier and why HOG plus Linear SVM was selected.

**Key technical point:** The model predicts only physical shape, not health.

**Possible question:** Why not use a deep CNN?

**Best answer:** The current dataset is small. A lightweight HOG + SVM model is explainable, fast, and performed best in the comparison.

## Slide 9: Digital Battery Passport

**What I should say:** I explain the passport as a traceable record for each battery.

**Key technical point:** The passport stores input features, predictions, and final decisions.

**Possible question:** Are all passport fields real?

**Best answer:** The project supports the structure, but in this prototype sensor fields are mock values because real BMS integration is future work.

## Slide 10: SOH Prediction Method

**What I should say:** I explain the SOH formula and how ML estimates SOH at runtime.

**Key technical point:** Capacity creates the target; sensor-style features are used for prediction.

**Possible question:** Why use ML if the formula exists?

**Best answer:** The formula requires capacity. At inference, capacity may not be directly available, so ML estimates SOH from available health parameters.

## Slide 11: ML Model Comparison

**What I should say:** I compare five regression models and show why Random Forest was selected.

**Key technical point:** Random Forest achieved the lowest RMSE and MAE on the held-out split.

**Possible question:** Why did Random Forest perform best?

**Best answer:** The SOH relationship is nonlinear and depends on feature interactions, so tree ensembles handle it better than a linear baseline on this tabular dataset.

## Slide 12: Re-X Decision Engine

**What I should say:** I explain the decision rules and safety overrides.

**Key technical point:** A high predicted SOH can still be quarantined if safety measurements are abnormal.

**Possible question:** Why quarantine high-SOH batteries?

**Best answer:** SOH alone is not enough. Very high temperature, abnormal voltage, or high resistance indicate safety risk, so quarantine is the safer route.

## Slide 13: Unity Digital Twin

**What I should say:** I explain what Unity visualizes and what is simulated.

**Key technical point:** Unity is connected to the backend API for classification and SOH decisions.

**Possible question:** Are the Unity sensors real?

**Best answer:** No. In this prototype Unity generates mock sensor values. The architecture is ready to replace them with real sensor or BMS data.

## Slide 14: Robotic Sorting Workflow

**What I should say:** I describe the physical sorting sequence from inspection to bin placement.

**Key technical point:** Robot sorting is driven by backend target_bin values.

**Possible question:** Is a real robot controlled?

**Best answer:** At this stage the robot is simulated in Unity. Real robot control is future work.

## Slide 15: Backend API

**What I should say:** I explain the API endpoints used by Unity and the model reporting endpoint.

**Key technical point:** The key runtime endpoint for stage two is /predict-soh.

**Possible question:** Is /train-soh-model implemented?

**Best answer:** Not as an API endpoint. Training is implemented as a reproducible script, and model metrics are exposed through /soh-model-metrics.

## Slide 16: Example End-to-End Case

**What I should say:** I show one concrete API result from the implemented backend.

**Key technical point:** The backend returns both SOH and routing information for Unity.

**Possible question:** Why is SOH different from the prompt's example?

**Best answer:** I used the actual trained model output from the current project rather than a placeholder, so the slide remains technically honest.

## Slide 17: Results / Demo Outputs

**What I should say:** I summarize the current measured software outputs.

**Key technical point:** The table includes real backend model outputs and a safety override example.

**Possible question:** Are these production test results?

**Best answer:** No. They are prototype software validation outputs. Industrial validation would require real sensors, BMS data, and factory testing.

## Slide 18: Implementation Status

**What I should say:** I give a transparent feature-by-feature status table.

**Key technical point:** This slide separates implemented software from simulated and planned hardware work.

**Possible question:** What is the strongest implemented part?

**Best answer:** The backend CV and SOH pipeline, model artifacts, API endpoints, and Unity integration are implemented and verified.

## Slide 19: Limitations

**What I should say:** I explain the boundaries of the current prototype.

**Key technical point:** The system is honest about mock inputs, limited data, and missing industrial validation.

**Possible question:** Does this limitation weaken the project?

**Best answer:** No. It defines the current maturity level and gives a clear path for future validation.

## Slide 20: Future Work

**What I should say:** I present the roadmap from prototype to industrial-grade system.

**Key technical point:** The immediate priority is replacing mock inputs with real BMS or sensor readings.

**Possible question:** Which future item is most important?

**Best answer:** Real health data integration is most important because it directly improves SOH reliability and decision validity.

## Slide 21: Conclusion

**What I should say:** I close by summarizing the main contribution and the honest scope.

**Key technical point:** The contribution is the integrated architecture and implemented software pipeline.

**Possible question:** What is the main contribution?

**Best answer:** A working, explainable prototype that links battery type recognition, SOH prediction, Re-X routing, and digital twin visualization.

## Slide 22: Q&A

**What I should say:** I invite questions and return to the main message if needed.

**Key technical point:** The system is an explainable prototype with a clear validation roadmap.

**Possible question:** What should be improved first?

**Best answer:** The first improvement should be real health data integration, because it removes the biggest prototype assumption.
