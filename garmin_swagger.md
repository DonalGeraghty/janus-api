# Garmin Connect Personal API

API version: **1.0.0**  
Specification shown by source: **OpenAPI 3**  
Base URL: `https://personal.connectapi.garmin.com`

Formatted from copied Swagger UI text; this is not a machine-readable OpenAPI specification. Collapsed schema values (`{...}`, `[...]`, and enum counts) are preserved as supplied. Their hidden details are unavailable in this copy.

## Contents

- [activity-service](#activity-service)
- [activitylist-service](#activitylist-service)
- [biometric-service](#biometric-service)
- [download-service](#download-service)
- [fitnessage-service](#fitnessage-service)
- [goal-service](#goal-service)
- [hrv-service](#hrv-service)
- [nutrition-service](#nutrition-service)
- [periodichealth-service](#periodichealth-service)
- [sleep-service](#sleep-service)
- [userprofile-service](#userprofile-service)
- [usersummary-service](#usersummary-service)
- [weight-service](#weight-service)
- [wellness-service](#wellness-service)
- [wellnessactivity-service](#wellnessactivity-service)
- [Schemas](#schemas)

## Endpoint index

| Method | Path |
| --- | --- |
| `GET` | `/activity-service/activity/{activityId}` |
| `GET` | `/activity-service/activity/{activityId}/workouts` |
| `GET` | `/activitylist-service/activities/search/activities` |
| `GET` | `/biometric-service/heartRateZones/v2` |
| `GET` | `/download-service/files/activity/{activityId}` |
| `GET` | `/fitnessage-service/fitnessage/v2/{calendarDate}` |
| `GET` | `/goal-service/goal/user/effective/weightgoal/{startDate}/{endDate}` |
| `GET` | `/hrv-service/hrv/{calendarDate}` |
| `GET` | `/hrv-service/hrv/daily/{fromDate}/{toDate}` |
| `GET` | `/nutrition-service/food/logs/{date}` |
| `GET` | `/periodichealth-service/menstrualcycle/summary/{calendarDate}` |
| `GET` | `/periodichealth-service/menstrualcycle/dayview/{calendarDate}` |
| `GET` | `/sleep-service/sleep/dailySleep` |
| `GET` | `/sleep-service/sleep/dailySleepSummariesByDate` |
| `GET` | `/userprofile-service/userprofile/settings` |
| `GET` | `/usersummary-service/stats/hydration/daily/{startDate}/{endDate}` |
| `GET` | `/usersummary-service/stats/steps/daily/{startDate}/{endDate}` |
| `GET` | `/usersummary-service/stats/stress/daily/{startDate}/{endDate}` |
| `GET` | `/usersummary-service/usersummary/daily` |
| `GET` | `/usersummary-service/v2/dailysummaries` |
| `GET` | `/weight-service/weight/all/{startDate}/{endDate}` |
| `GET` | `/weight-service/weight/range/{startDate}/{endDate}` |
| `GET` | `/wellness-service/wellness/bodyBattery/reports/daily` |
| `GET` | `/wellness-service/wellness/daily/spo2acclimation/{calendarDate}` |
| `GET` | `/wellness-service/wellness/dailyHeartRate` |
| `GET` | `/wellnessactivity-service/activity/summary/range/{fromDate}/{untilDate}` |

## activity-service

Retrieve an activity's summary, metadata, measurements, split summary, and associated workouts.

### GET `/activity-service/activity/{activityId}`

Retrieves the activity summary, metadata, measurements, and split summary information for the specified activity.

#### Parameters

```text
activityId *
integer($int64)
(path)
The ID of the activity to retrieve the summary

activityId
```

#### Responses

##### 200

Activity summary returned successfully

Content type: `application/json`

```json
{
  "activityId": 0,
  "activityUUID": {
    "uuid": "string"
  },
  "activityName": "string",
  "description": "string",
  "userProfileId": 0,
  "parentId": 0,
  "parentName": "string",
  "isMultiSportParent": true,
  "activityTypeDTO": {
    "typeId": 1,
    "typeKey": "running",
    "parentTypeId": 17
  },
  "eventTypeDTO": {
    "typeId": 0,
    "typeKey": "race"
  },
  "accessControlRuleDTO": {
    "typeId": 0,
    "typeKey": "private"
  },
  "timeZoneUnitDTO": {
    "unitId": 152,
    "unitKey": "America/Chicago",
    "timeZone": "America/Chicago"
  },
  "metadataDTO": {
    "isOriginal": true,
    "fileFormat": {
      "formatId": 7,
      "formatKey": "fit"
    },
    "lastUpdateDate": "2022-08-10T09:47:59.031",
    "uploadedDate": "2022-08-10T09:47:59.031",
    "videoUrl": "string",
    "userInfoDto": {
      "userProfilePk": 0,
      "displayname": "string",
      "fullname": "string",
      "profileImageUrlLarge": "string",
      "profileImageUrlMedium": "string",
      "profileImageUrlSmall": "string"
    },
    "childIds": [
      0
    ],
    "childActivityTypes": [
      "string"
    ],
    "sensors": [
      {
        "manufacturer": "GARMIN",
        "serialNumber": 30218472,
        "sku": "006-B2900-00",
        "fitProductNumber": 2900,
        "sourceType": "ANTPLUS",
        "antplusDeviceType": "HEART_RATE",
        "localDeviceType": "WHR",
        "bodyLocation": "WAIST_MID_BACK",
        "softwareVersion": 1.18,
        "batteryStatus": "GOOD",
        "bleDeviceType": "BIKE_TRAINER",
        "productName": "HRM-Pro",
        "batteryLevel": 85
      }
    ],
    "activityImages": [
      {
        "url": "string",
        "smallUrl": "string",
        "mediumUrl": "string",
        "expirationTimestamp": 0
      }
    ],
    "manufacturer": "string",
    "lapCount": 0,
    "eBikeMaxAssistModes": 0,
    "eBikeBatteryUsage": 0,
    "eBikeBatteryRemaining": 0,
    "eBikeAssistModeInfoDTOList": [
      {
        "ebikeAssistMode": 0,
        "ebikeAssistModeName": "Eco"
      }
    ],
    "hasRunPowerWindData": true,
    "calendarEventInfo": {
      "completionTargetValue": 0,
      "completionTargetUnitType": "distance",
      "customGoalValue": 0,
      "customGoalUnitType": "distance"
    },
    "isWheelchair": true,
    "specializedWorkoutCategories": [
      "string"
    ],
    "hasMultiDayActivities": true,
    "personalRecord": true,
    "gcj02": true,
    "runPowerWindDataEnabled": true,
    "trimmed": true,
    "manualActivity": true,
    "elevationCorrected": true,
    "autoCalcCalories": true,
    "favorite": true
  },
  "summaryDTO": {
    "startTimeLocal": "2022-08-10T09:47:59.031",
    "startTimeGMT": "2022-08-10T09:47:59.031",
    "startLatitude": 0,
    "startLongitude": 0,
    "distance": 0,
    "duration": 0,
    "movingDuration": 0,
    "elapsedDuration": 0,
    "elevationGain": 0,
    "elevationLoss": 0,
    "maxElevation": 0,
    "minElevation": 0,
    "avgElevation": 0,
    "averageSpeed": 0,
    "averageMovingSpeed": 0,
    "maxSpeed": 0,
    "calories": 0,
    "bmrCalories": 0,
    "averageHR": 0,
    "maxHR": 0,
    "minHR": 0,
    "averageRunCadence": 0,
    "maxRunCadence": 0,
    "maxLapAvgRunCadence": 0,
    "averageBikeCadence": 0,
    "maxBikeCadence": 0,
    "averageSwimCadence": 0,
    "maxSwimCadence": 0,
    "averageTemperature": 0,
    "maxTemperature": 0,
    "minTemperature": 0,
    "averagePower": 0,
    "maxPower": 0,
    "maxPowerTwentyMinutes": 0,
    "minPower": 0,
    "normalizedPower": 0,
    "functionalThresholdPower": 0,
    "totalWork": 0,
    "leftBalance": 0,
    "rightBalance": 0,
    "leftTorqueEffectiveness": 0,
    "rightTorqueEffectiveness": 0,
    "leftPedalSmoothness": 0,
    "rightPedalSmoothness": 0,
    "groundContactTime": 0,
    "groundContactBalanceLeft": 0,
    "strideLength": 0,
    "verticalOscillation": 0,
    "trainingEffect": 0,
    "anaerobicTrainingEffect": 0,
    "aerobicTrainingEffectMessage": "MINOR_AEROBIC_BENEFIT_0",
    "anaerobicTrainingEffectMessage": "NO_ANAEROBIC_BENEFIT_0",
    "trainingStressScore": 0,
    "intensityFactor": 0,
    "poolLength": 0,
    "numberOfActiveLengths": 0,
    "unitOfPoolLength": {
      "unitKey": "kilogram"
    },
    "totalNumberOfStrokes": 0,
    "averageStrokes": 0,
    "minimumStrokes": 0,
    "averageSWOLF": 0,
    "minSWOLF": 0,
    "strokeDistance": 0,
    "standingCount": 0,
    "seatedTime": 0,
    "standingTime": 0,
    "maxSeatedPower": 0,
    "maxStandingPower": 0,
    "averageSeatedPower": 0,
    "averageStandingPower": 0,
    "maxSeatedCadence": 0,
    "maxStandingCadence": 0,
    "averageSeatedCadence": 0,
    "averageStandingCadence": 0,
    "leftPowerPhaseStart": 0,
    "leftPowerPhaseEnd": 0,
    "leftPowerPhaseArcLength": 0,
    "leftPowerPhaseArcCenter": 0,
    "leftPowerPhasePeakStart": 0,
    "leftPowerPhasePeakEnd": 0,
    "leftPowerPhasePeakArcLength": 0,
    "leftPowerPhasePeakArcCenter": 0,
    "leftPlatformCenterOffset": 0,
    "rightPowerPhaseStart": 0,
    "rightPowerPhaseEnd": 0,
    "rightPowerPhaseArcLength": 0,
    "rightPowerPhaseArcCenter": 0,
    "rightPowerPhasePeakStart": 0,
    "rightPowerPhasePeakEnd": 0,
    "rightPowerPhasePeakArcLength": 0,
    "rightPowerPhasePeakArcCenter": 0,
    "rightPlatformCenterOffset": 0,
    "lactateThresholdHeartRate": 0,
    "averageGforce": 0,
    "maxGforce": 0,
    "verticalRatio": 0,
    "lactateThresholdSpeed": 0,
    "directFunctionalThresholdPower": 0,
    "distancePerStroke": 0,
    "strokeCadence": 0,
    "averageStrokeDistance": 0,
    "averageStrokeCadence": 0,
    "maxStrokeCadence": 0,
    "riderPosition": 0,
    "startTimeGMTDoubleValue": 0,
    "totalExerciseReps": 0,
    "totalReps": 0,
    "totalSets": 0,
    "activeSets": 0,
    "maxLapRepCount": 0,
    "maxDepth": 0,
    "averageDepth": 0,
    "surfaceInterval": 0,
    "startCns": 0,
    "endCns": 0,
    "startN2": 0,
    "endN2": 0,
    "bottomTime": 0,
    "maxBottomTime": 0,
    "diveAlert": "string",
    "endLatitude": 0,
    "endLongitude": 0,
    "isDecoDive": true,
    "floorsClimbed": 0,
    "floorsDescended": 0,
    "avgVerticalSpeed": 0,
    "maxVerticalSpeed": 0,
    "perceivedWorkoutEffort": 0,
    "flow": 0,
    "grit": 0,
    "jumpCount": 0,
    "caloriesEstimated": 0,
    "caloriesConsumed": 0,
    "waterEstimated": 0,
    "waterConsumed": 0,
    "minRespirationRate": 0,
    "maxRespirationRate": 0,
    "avgRespirationRate": 0,
    "trainingEffectLabel": "string",
    "activityTrainingLoad": 0,
    "avgFlow": 0,
    "avgGrit": 0,
    "minActivityLapDuration": 0,
    "startStress": 0,
    "endStress": 0,
    "differenceStress": 0,
    "directWorkoutFeel": 0,
    "directWorkoutRpe": 0,
    "directWorkoutComplianceScore": 0,
    "targetDuration": 0,
    "targetDistance": 0,
    "targetAverageSpeed": 0,
    "moderateIntensityMinutes": 0,
    "vigorousIntensityMinutes": 0,
    "steps": 0,
    "avgStress": 100,
    "maxStress": 100,
    "recoveryHeartRate": 0,
    "beginPotentialStamina": 0,
    "endPotentialStamina": 0,
    "minAvailableStamina": 0,
    "gainSolarActivityTime": 0,
    "avgSolarChargePercent": 0,
    "avgEbikeAssistLevelPercent": 0,
    "avgGradeAdjustedSpeed": 0,
    "avgWheelchairCadence": 0,
    "maxWheelchairCadence": 0,
    "avgJumpRopeCadence": 0,
    "maxJumpRopeCadence": 0,
    "avgElapsedDurationVerticalSpeed": 0,
    "surfaceTypeUnpavedPercentage": 0,
    "differenceBodyBattery": 0,
    "beginPackWeight": 0,
    "impactLoad": 0,
    "stepSpeedLoss": 0,
    "stepSpeedLossPercent": 0,
    "diveCount": 0,
    "longestPoolApneaInterval": 0,
    "avgForce": 0,
    "maxForce": 0,
    "normalizedForce": 0,
    "poolApneaBreathHoldDuration": 0,
    "avgSpo2": 0,
    "minSpo2": 0,
    "maxSpo2": 0,
    "carbonOffset": 0,
    "packWeightCalories": 0,
    "decoDive": true
  },
  "locationName": "string",
  "diveInfo": {
    "weight": 6,
    "weightUnit": {
      "unitKey": "kilogram"
    },
    "exposureSuit": "Wetsuit",
    "suitThickness": 5,
    "visibility": 15,
    "visibilityUnit": {
      "unitKey": "meter"
    },
    "surfaceCondition": "Calm",
    "current": "Mild",
    "entryType": "Shore",
    "equipments": "Mask, fins, and buoyancy compensator",
    "buddy": "string",
    "diveSettings": {
      "name": "Default",
      "model": 0,
      "gfLow": 30,
      "gfHigh": 70,
      "waterType": 1,
      "waterDensity": 1025,
      "ccrLowSetpointSwitchMode": 1,
      "ccrLowSetpoint": 0.7,
      "ccrLowSetpointDepth": 6,
      "ccrHighSetpointSwitchMode": 0,
      "ccrHighSetpoint": 1.3,
      "ccrHighSetpointDepth": 20
    },
    "diveGases": [
      {
        "heliumContent": 0,
        "oxygenContent": 21,
        "status": 1,
        "gasIndex": 0,
        "volume": 12,
        "volumeUnit": {
          "unitKey": "liter"
        },
        "tankType": "Steel",
        "tankStartingPressure": 200,
        "tankStartingPressureUnit": {
          "unitKey": "bar"
        },
        "tankEndingPressure": 50,
        "tankEndingPressureUnit": {
          "unitKey": "bar"
        },
        "tankSize": 12,
        "tankSizeUnit": {
          "unitKey": "liter"
        },
        "sacRate": 15,
        "gasMode": 0
      }
    ],
    "totalSurfaceTime": 300
  },
  "splitSummaries": [
    {
      "startTimeLocal": "2022-08-10T09:47:59.031",
      "startTimeGMT": "2022-08-10T09:47:59.031",
      "startLatitude": 0,
      "startLongitude": 0,
      "distance": 0,
      "duration": 0,
      "movingDuration": 0,
      "elapsedDuration": 0,
      "elevationGain": 0,
      "elevationLoss": 0,
      "maxElevation": 0,
      "minElevation": 0,
      "avgElevation": 0,
      "averageSpeed": 0,
      "averageMovingSpeed": 0,
      "maxSpeed": 0,
      "calories": 0,
      "bmrCalories": 0,
      "averageHR": 0,
      "maxHR": 0,
      "minHR": 0,
      "averageRunCadence": 0,
      "maxRunCadence": 0,
      "maxLapAvgRunCadence": 0,
      "averageBikeCadence": 0,
      "maxBikeCadence": 0,
      "averageSwimCadence": 0,
      "maxSwimCadence": 0,
      "averageTemperature": 0,
      "maxTemperature": 0,
      "minTemperature": 0,
      "averagePower": 0,
      "maxPower": 0,
      "maxPowerTwentyMinutes": 0,
      "minPower": 0,
      "normalizedPower": 0,
      "functionalThresholdPower": 0,
      "totalWork": 0,
      "leftBalance": 0,
      "rightBalance": 0,
      "leftTorqueEffectiveness": 0,
      "rightTorqueEffectiveness": 0,
      "leftPedalSmoothness": 0,
      "rightPedalSmoothness": 0,
      "groundContactTime": 0,
      "groundContactBalanceLeft": 0,
      "strideLength": 0,
      "verticalOscillation": 0,
      "trainingEffect": 0,
      "anaerobicTrainingEffect": 0,
      "aerobicTrainingEffectMessage": "MINOR_AEROBIC_BENEFIT_0",
      "anaerobicTrainingEffectMessage": "NO_ANAEROBIC_BENEFIT_0",
      "trainingStressScore": 0,
      "intensityFactor": 0,
      "poolLength": 0,
      "numberOfActiveLengths": 0,
      "unitOfPoolLength": {
        "unitKey": "kilogram"
      },
      "totalNumberOfStrokes": 0,
      "averageStrokes": 0,
      "minimumStrokes": 0,
      "averageSWOLF": 0,
      "minSWOLF": 0,
      "strokeDistance": 0,
      "standingCount": 0,
      "seatedTime": 0,
      "standingTime": 0,
      "maxSeatedPower": 0,
      "maxStandingPower": 0,
      "averageSeatedPower": 0,
      "averageStandingPower": 0,
      "maxSeatedCadence": 0,
      "maxStandingCadence": 0,
      "averageSeatedCadence": 0,
      "averageStandingCadence": 0,
      "leftPowerPhaseStart": 0,
      "leftPowerPhaseEnd": 0,
      "leftPowerPhaseArcLength": 0,
      "leftPowerPhaseArcCenter": 0,
      "leftPowerPhasePeakStart": 0,
      "leftPowerPhasePeakEnd": 0,
      "leftPowerPhasePeakArcLength": 0,
      "leftPowerPhasePeakArcCenter": 0,
      "leftPlatformCenterOffset": 0,
      "rightPowerPhaseStart": 0,
      "rightPowerPhaseEnd": 0,
      "rightPowerPhaseArcLength": 0,
      "rightPowerPhaseArcCenter": 0,
      "rightPowerPhasePeakStart": 0,
      "rightPowerPhasePeakEnd": 0,
      "rightPowerPhasePeakArcLength": 0,
      "rightPowerPhasePeakArcCenter": 0,
      "rightPlatformCenterOffset": 0,
      "lactateThresholdHeartRate": 0,
      "averageGforce": 0,
      "maxGforce": 0,
      "verticalRatio": 0,
      "lactateThresholdSpeed": 0,
      "directFunctionalThresholdPower": 0,
      "distancePerStroke": 0,
      "strokeCadence": 0,
      "averageStrokeDistance": 0,
      "averageStrokeCadence": 0,
      "maxStrokeCadence": 0,
      "riderPosition": 0,
      "startTimeGMTDoubleValue": 0,
      "totalExerciseReps": 0,
      "totalReps": 0,
      "totalSets": 0,
      "activeSets": 0,
      "maxLapRepCount": 0,
      "maxDepth": 0,
      "averageDepth": 0,
      "surfaceInterval": 0,
      "startCns": 0,
      "endCns": 0,
      "startN2": 0,
      "endN2": 0,
      "bottomTime": 0,
      "maxBottomTime": 0,
      "diveAlert": "string",
      "endLatitude": 0,
      "endLongitude": 0,
      "isDecoDive": true,
      "floorsClimbed": 0,
      "floorsDescended": 0,
      "avgVerticalSpeed": 0,
      "maxVerticalSpeed": 0,
      "perceivedWorkoutEffort": 0,
      "flow": 0,
      "grit": 0,
      "jumpCount": 0,
      "caloriesEstimated": 0,
      "caloriesConsumed": 0,
      "waterEstimated": 0,
      "waterConsumed": 0,
      "minRespirationRate": 0,
      "maxRespirationRate": 0,
      "avgRespirationRate": 0,
      "trainingEffectLabel": "string",
      "activityTrainingLoad": 0,
      "avgFlow": 0,
      "avgGrit": 0,
      "minActivityLapDuration": 0,
      "startStress": 0,
      "endStress": 0,
      "differenceStress": 0,
      "directWorkoutFeel": 0,
      "directWorkoutRpe": 0,
      "directWorkoutComplianceScore": 0,
      "targetDuration": 0,
      "targetDistance": 0,
      "targetAverageSpeed": 0,
      "moderateIntensityMinutes": 0,
      "vigorousIntensityMinutes": 0,
      "steps": 0,
      "avgStress": 100,
      "maxStress": 100,
      "recoveryHeartRate": 0,
      "beginPotentialStamina": 0,
      "endPotentialStamina": 0,
      "minAvailableStamina": 0,
      "gainSolarActivityTime": 0,
      "avgSolarChargePercent": 0,
      "avgEbikeAssistLevelPercent": 0,
      "avgGradeAdjustedSpeed": 0,
      "avgWheelchairCadence": 0,
      "maxWheelchairCadence": 0,
      "avgJumpRopeCadence": 0,
      "maxJumpRopeCadence": 0,
      "avgElapsedDurationVerticalSpeed": 0,
      "surfaceTypeUnpavedPercentage": 0,
      "differenceBodyBattery": 0,
      "beginPackWeight": 0,
      "impactLoad": 0,
      "stepSpeedLoss": 0,
      "stepSpeedLossPercent": 0,
      "diveCount": 0,
      "longestPoolApneaInterval": 0,
      "avgForce": 0,
      "maxForce": 0,
      "normalizedForce": 0,
      "poolApneaBreathHoldDuration": 0,
      "avgSpo2": 0,
      "minSpo2": 0,
      "maxSpo2": 0,
      "carbonOffset": 0,
      "packWeightCalories": 0,
      "messageIndex": 0,
      "splitType": "PACE_PRO_SPLIT",
      "noOfSplits": 0,
      "averagePowerTarget": 0,
      "numFalls": 0,
      "numClimbSends": 0,
      "numClimbsAttempted": 0,
      "numClimbsCompleted": 0,
      "maxElevationGain": 0,
      "averageElevationGain": 0,
      "maxDistance": 0,
      "maxDistanceWithPrecision": 0,
      "maxGradeValue": {
        "valueKey": "_5_1",
        "scale": "YDS"
      },
      "mode": "ADVANCED",
      "gamesWon": 0,
      "swimStraightnessScore": 0,
      "swimStraightnessExtraDistance": 0,
      "weightedMeanBestFiveMaxSpeedOverTenSeconds": 0,
      "maxPisteDifficulty": "GREEN",
      "avgReactionTime": 0,
      "minReactionTime": 0,
      "avgStepFrequency": 0,
      "maxStepFrequency": 0,
      "gctAirTimeRatio": 0,
      "maxAcceleration": 0,
      "avgMaxAcceleration": 0,
      "avgMaxSpeed": 0,
      "minStanceTime": 0,
      "avgStanceTime": 0,
      "avgStanceTimePercent": 0,
      "avgStepLength": 0,
      "maxStepLength": 0,
      "avgDistanceToMaxSpeed": 0,
      "avgPackWeight": 0,
      "maxPackWeight": 0,
      "maxDuration": 0,
      "decoDive": true
    }
  ],
  "videoGameInfo": {
    "name": "string",
    "type": "GENERIC_WIN_LOSS_RESULT"
  },
  "deviceDisplayUnitsDTO": {
    "distanceDisplayMeasure": "string",
    "elevationDisplayMeasure": "string",
    "speedDisplayMeasure": "string",
    "verticalSpeedDisplayMeasure": "string"
  }
}
```

##### 400

The ID of the activity is missing or invalid.

##### 401

Authentication is missing or invalid.

##### 403

The caller is not authorized to access this activity.

##### 404

No activity exists for the specified activity ID.

##### 500

An unexpected server error occurred.

### GET `/activity-service/activity/{activityId}/workouts`

Retrieves workouts performed during an activity

#### Parameters

```text
activityId *
integer($int64)
(path)
The ID of the activity for which to retrieve workouts

activityId
```

#### Responses

##### 200

Workouts returned successfully. Returns an empty array when no workouts are found for the activity.

Content type: `application/json`

Examples

No workouts found for the activity

[]

##### 400

The ID of the activity is missing or invalid.

##### 401

Authentication is missing or invalid.

##### 403

The caller is not authorized to access this activity.

##### 404

No activity exists for the specified activity ID.

##### 500

An unexpected server error occurred.

## activitylist-service

Search a user's activities with filters and pagination, returning matching activity summaries.

### GET `/activitylist-service/activities/search/activities`

Searches activities using the supplied filters and returns matching paginated activity summaries.

#### Parameters

```text
start
integer($int32)
(query)
Zero-based offset of the first activity to return. Defaults to 0.

Default value : 0

0
limit
integer($int32)
(query)
Maximum number of activities to return. Defaults to 99.

Default value : 99

99
favorite
integer($int32)
(query)
Filter by favorite status: 1 returns favorites, 0 returns non-favorites, and -1 applies no favorite filter. Defaults to -1.

Default value : -1

-1
sortOrder
string
(query)
Sort direction: asc for ascending or desc for descending, case-insensitive. Defaults to desc.

Default value : desc

desc
excludeChildren
boolean
(query)
Whether to exclude child activities that have a parent activity, such as individual legs of a multisport activity. Defaults to true.

Default value : true


true
sortBy
string
(query)
Activity field to sort by, such as name, distance, or duration. Defaults to startLocal, the activity's local start date and time.

sortBy
search
string
(query)
Text to search for in activity names and descriptions.

search
activityType
string
(query)
Parent activity type key to include, such as running or cycling. Must identify a parent type, not a subtype.

activityType
activitySubType
string
(query)
Activity subtype key to include. Must identify a child type and, if activityType is also provided, belong to that parent type. For example, use activitySubType=trail_running with activityType=running, or activitySubType=road_cycling with activityType=cycling.

activitySubType
eventType
string
(query)
Event classification key to include, such as race, training, recreation, fitness, specialEvent, or uncategorized.

eventType
minDistance
integer($int64)
(query)
Inclusive minimum activity distance, in meters.

minDistance
maxDistance
integer($int64)
(query)
Inclusive maximum activity distance, in meters.

maxDistance
minDuration
integer($int64)
(query)
Inclusive minimum activity timer duration, in seconds.

minDuration
maxDuration
integer($int64)
(query)
Inclusive maximum activity timer duration, in seconds.

maxDuration
minElevation
integer($int64)
(query)
Inclusive minimum total elevation gain for the activity, in meters.

minElevation
maxElevation
integer($int64)
(query)
Inclusive maximum total elevation gain for the activity, in meters.

maxElevation
startDate
string($date)
(query)
Inclusive earliest activity start date, based on the activity's local start time, in YYYY-MM-DD format.

2026-08-31
endDate
string($date)
(query)
Inclusive latest activity start date, based on the activity's local start time, in YYYY-MM-DD format.

2026-08-31
upperLatitude
number($double)
(query)
Northern latitude boundary of the bounding box for activity start locations, in decimal degrees. Provide all four latitude and longitude boundaries to apply this filter.

upperLatitude
rightLongitude
number($double)
(query)
Eastern longitude boundary of the bounding box for activity start locations, in decimal degrees. Provide all four latitude and longitude boundaries to apply this filter.

rightLongitude
lowerLatitude
number($double)
(query)
Southern latitude boundary of the bounding box for activity start locations, in decimal degrees. Provide all four latitude and longitude boundaries to apply this filter.

lowerLatitude
leftLongitude
number($double)
(query)
Western longitude boundary of the bounding box for activity start locations, in decimal degrees. Provide all four latitude and longitude boundaries to apply this filter.

leftLongitude
lowerMaxDepth
integer($int64)
(query)
Inclusive lower bound on the dive activity's maximum depth, in centimeters.

lowerMaxDepth
upperMaxDepth
integer($int64)
(query)
Inclusive upper bound on the dive activity's maximum depth, in centimeters.

upperMaxDepth
decoDive
boolean
(query)
Filter by decompression dive status: true returns decompression dives and false returns activities marked as non-decompression dives. Omit to apply no decompression dive filter.


--
minElapsedDuration
integer($int64)
(query)
Inclusive minimum total elapsed activity duration, including paused time, in seconds.

minElapsedDuration
maxElapsedDuration
integer($int64)
(query)
Inclusive maximum total elapsed activity duration, including paused time, in seconds.

maxElapsedDuration
minBottomTime
integer($int64)
(query)
Inclusive minimum dive bottom time, in seconds.

minBottomTime
maxBottomTime
integer($int64)
(query)
Inclusive maximum dive bottom time, in seconds.

maxBottomTime
minAvgPower
integer($int64)
(query)
Inclusive minimum average activity power, in watts.

minAvgPower
excludedActivitySubType
array[string]
(query)
Activity subtype keys to exclude. Repeat this query parameter to exclude multiple subtypes.

requiredField
array[string]
(query)
Activity fields that must have a non-null value for an activity to be included. Repeat this query parameter to require multiple fields; all specified fields must be present.
```

#### Responses

##### 200

Returns an array of activity summaries matching the supplied filters and pagination. Returns an empty array when no results are found for the provided query parameters.

Content type: `application/json`

```json
[
  {
    "activityId": 0,
    "activityName": "string",
    "description": "string",
    "startTimeLocal": "2026-08-31 17:01:18",
    "startTimeGMT": "2026-08-31 22:01:18",
    "activityType": {
      "typeId": 1,
      "typeKey": "running",
      "parentTypeId": 17
    },
    "eventType": {
      "typeId": 0,
      "typeKey": "race"
    },
    "comments": [
      {
        "conversationCommentUuid": "string",
        "conversationCommentPk": 0,
        "conversationUuid": "string",
        "activityCommentPk": 0,
        "authorSocProfilePk": 0,
        "authorDisplayName": "string",
        "authorFullName": "string",
        "authorUserProfilePk": 0,
        "authorImageUrl": "string",
        "body": "string",
        "activityId": 0,
        "activityCommentLikeCount": 0,
        "requestorCanEdit": true,
        "requestorCanDelete": true,
        "authorPro": true,
        "createDate": "2026-10-22T18:24:56.059Z",
        "lastUpdatedDate": "2026-10-22T18:24:56.059Z",
        "activityCommentLikedByUser": true,
        "activityCommentLikeDisplayNames": [
          "string"
        ],
        "activityCommentLikeFullNames": [
          "string"
        ],
        "groupPk": 0,
        "activityCommentLikeAuthors": [
          {
            "userProfilePk": 0,
            "displayname": "string",
            "fullname": "string",
            "profileImageUrlLarge": "string",
            "profileImageUrlMedium": "string",
            "profileImageUrlSmall": "string"
          }
        ]
      }
    ],
    "isFavorite": true,
    "isPR": true,
    "isAutoCalcCalories": true,
    "isParent": true,
    "parentId": 0,
    "distance": 0,
    "duration": 2400.931884765625,
    "elapsedDuration": 2404.966064453125,
    "movingDuration": 2396.947021484375,
    "elevationGain": 0,
    "elevationLoss": 0,
    "averageSpeed": 0,
    "maxSpeed": 0,
    "startLatitude": 0,
    "startLongitude": 0,
    "hasPolyline": true,
    "hasImages": true,
    "ownerId": 0,
    "ownerDisplayName": "string",
    "ownerFullName": "string",
    "ownerProfileImageUrlSmall": "string",
    "ownerProfileImageUrlMedium": "string",
    "ownerProfileImageUrlLarge": "string",
    "calories": 0,
    "bmrCalories": 0,
    "averageHR": 0,
    "maxHR": 0,
    "averageRunningCadenceInStepsPerMinute": 0,
    "maxRunningCadenceInStepsPerMinute": 0,
    "maxLapAvgRunCadence": 0,
    "averageBikingCadenceInRevPerMinute": 0,
    "maxBikingCadenceInRevPerMinute": 0,
    "averageSwimCadenceInStrokesPerMinute": 0,
    "maxSwimCadenceInStrokesPerMinute": 0,
    "averageSwolf": 0,
    "activeLengths": 0,
    "steps": 0,
    "numberOfActivityLikes": 0,
    "numberOfActivityComments": 0,
    "likedByUser": true,
    "commentedByUser": true,
    "activityLikeDisplayNames": [
      "string"
    ],
    "activityLikeFullNames": [
      "string"
    ],
    "activityLikeProfileImageUrls": [
      "string"
    ],
    "requestorRelationship": "string",
    "privacy": {
      "typeId": 0,
      "typeKey": "private"
    },
    "poolLength": 0,
    "unitOfPoolLength": {
      "unitKey": "kilogram"
    },
    "hasVideo": true,
    "videoUrl": "string",
    "beginTimestamp": 1788213678000,
    "sportTypeId": 0,
    "avgPower": 0,
    "maxPower": 0,
    "aerobicTrainingEffect": 0,
    "anaerobicTrainingEffect": 0,
    "strokes": 0,
    "normPower": 0,
    "leftBalance": 0,
    "rightBalance": 0,
    "avgLeftBalance": 0,
    "max20MinPower": 0,
    "avgVerticalOscillation": 0,
    "avgGroundContactTime": 0,
    "avgStrideLength": 0,
    "avgFractionalCadence": 0,
    "maxFractionalCadence": 0,
    "trainingStressScore": 0,
    "intensityFactor": 0,
    "vO2MaxValue": 0,
    "avgVerticalRatio": 0,
    "avgGroundContactBalance": 0,
    "lactateThresholdBpm": 0,
    "getlactateThresholdSpeed": 0,
    "maxFtp": 0,
    "avgStrokeDistance": 0,
    "avgStrokeCadence": 0,
    "maxStrokeCadence": 0,
    "avgStrokes": 0,
    "minStrokes": 0,
    "minTemperature": 0,
    "maxTemperature": 0,
    "minElevation": 0,
    "maxElevation": 0,
    "avgElevation": 0,
    "avgDoubleCadence": 0,
    "maxDoubleCadence": 0,
    "isElevationCorrected": true,
    "summarizedExerciseSets": [
      {
        "category": "string",
        "subCategory": "string",
        "reps": 0,
        "volume": 0,
        "duration": 0,
        "sets": 0,
        "maxWeight": 0,
        "peakPower": 0,
        "concentricMeanVelocity": 0
      }
    ],
    "maxDepth": 0,
    "avgDepth": 0,
    "surfaceInterval": 0,
    "startN2": 0,
    "endN2": 0,
    "startCns": 0,
    "endCns": 0,
    "isDecoDive": true,
    "summarizedDiveInfo": {
      "weight": 0,
      "weightUnit": {
        "unitKey": "kilogram"
      },
      "visibility": 0,
      "visibilityUnit": {
        "unitKey": "kilogram"
      },
      "surfaceCondition": "string",
      "current": "string",
      "waterType": 0,
      "waterDensity": 0,
      "summarizedDiveGases": [
        {
          "heliumContent": 0,
          "oxygenContent": 0,
          "gasIndex": 0,
          "gasMode": 0
        }
      ],
      "totalSurfaceTime": 0
    },
    "diveCount": 0,
    "activityLikeAuthors": [
      {
        "userProfilePk": 0,
        "displayname": "string",
        "fullname": "string",
        "profileImageUrlLarge": "string",
        "profileImageUrlMedium": "string",
        "profileImageUrlSmall": "string"
      }
    ],
    "avgVerticalSpeed": 0,
    "maxVerticalSpeed": 0,
    "floorsClimbed": 0,
    "floorsDescended": 0,
    "manufacturer": "string",
    "diveNumber": 0,
    "locationName": "string",
    "bottomTime": 0,
    "lapCount": 0,
    "endLatitude": 0,
    "endLongitude": 0,
    "flow": 0,
    "grit": 0,
    "jumpCount": 0,
    "caloriesEstimated": 0,
    "caloriesConsumed": 0,
    "waterEstimated": 0,
    "waterConsumed": 0,
    "maxAvgPower_1": 0,
    "maxAvgPower_2": 0,
    "maxAvgPower_5": 0,
    "maxAvgPower_10": 0,
    "maxAvgPower_20": 0,
    "maxAvgPower_30": 0,
    "maxAvgPower_60": 0,
    "maxAvgPower_120": 0,
    "maxAvgPower_300": 0,
    "maxAvgPower_600": 0,
    "maxAvgPower_1200": 0,
    "maxAvgPower_1800": 0,
    "maxAvgPower_3600": 0,
    "maxAvgPower_7200": 0,
    "maxAvgPower_18000": 0,
    "excludeFromPowerCurveReports": true,
    "totalSets": 0,
    "activeSets": 0,
    "totalReps": 0,
    "minRespirationRate": 0,
    "maxRespirationRate": 0,
    "avgRespirationRate": 0,
    "trainingEffectLabel": "string",
    "activityTrainingLoad": 0,
    "avgFlow": 0,
    "avgGrit": 0,
    "minActivityLapDuration": 1199.947021484375,
    "avgStress": 0,
    "startStress": 0,
    "endStress": 0,
    "differenceStress": 0,
    "maxStress": 0,
    "aerobicTrainingEffectMessage": "string",
    "anaerobicTrainingEffectMessage": "string",
    "splitSummaries": [
      {
        "noOfSplits": 0,
        "maxGradeValue": {
          "valueKey": "_5_1",
          "scale": "YDS"
        },
        "totalAscent": 0,
        "duration": 0,
        "splitType": "PACE_PRO_SPLIT",
        "numClimbSends": 0,
        "maxElevationGain": 0,
        "averageElevationGain": 0,
        "maxDistance": 0,
        "maxDistanceWithPrecision": 0,
        "distance": 0,
        "averageSpeed": 0,
        "maxSpeed": 0,
        "mode": "ADVANCED",
        "numFalls": 0,
        "avgStress": 0,
        "avgStressWin": 0,
        "avgStressLoss": 0,
        "avgStressDraw": 0,
        "gamesWon": 0,
        "gamesNotWon": 0,
        "gamesAverageWon": 0,
        "elevationLoss": 0,
        "maxPackWeight": 0,
        "avgPackWeight": 0,
        "maxDuration": 0,
        "avgReactionTime": 0,
        "minReactionTime": 0,
        "avgDistanceToMaxSpeed": 0,
        "avgStepFrequency": 0,
        "maxStepFrequency": 0,
        "avgStepLength": 0,
        "verticalRatio": 0,
        "verticalOscillation": 0,
        "avgGroundContactBalanceLeft": 0,
        "avgGroundContactTime": 0,
        "avgStanceTimePercent": 0
      }
    ],
    "isManualActivity": true,
    "moderateIntensityMinutes": 0,
    "vigorousIntensityMinutes": 0,
    "maxBottomTime": 0,
    "hasSeedFirstbeatProfile": true,
    "avgGradeAdjustedSpeed": 0,
    "avgWheelchairCadence": 0,
    "maxWheelchairCadence": 0,
    "avgJumpRopeCadence": 0,
    "maxJumpRopeCadence": 0,
    "gameName": "string",
    "differenceBodyBattery": 100,
    "gameType": "GENERIC_WIN_LOSS_RESULT",
    "beginPackWeight": 0,
    "fastestSplit_1000": 0,
    "fastestSplit_1609": 0,
    "fastestSplit_5000": 0,
    "fastestSplit_10000": 0,
    "fastestSplit_21098": 0,
    "fastestSplit_42195": 0,
    "fastestSplit_40000": 0,
    "fastestSplit_100": 0,
    "fastestSplit_400": 0,
    "fastestSplit_750": 0,
    "fastestSplit_1500": 0,
    "fastestSplit_91": 0,
    "fastestSplit_457": 0,
    "fastestSplit_914": 0,
    "fastestSplit_1508": 0,
    "impactLoad": 0,
    "avgStepSpeedLoss": 0,
    "avgStepSpeedLossPercent": 0,
    "hrTimeInZone_1": 6.001,
    "hrTimeInZone_2": 30,
    "hrTimeInZone_3": 793.001,
    "hrTimeInZone_4": 1120.344,
    "hrTimeInZone_5": 446.603,
    "powerTimeInZone_1": 351.933,
    "powerTimeInZone_2": 1300.59,
    "powerTimeInZone_3": 409.005,
    "powerTimeInZone_4": 224.005,
    "powerTimeInZone_5": 79.999,
    "powerTimeInZone_6": 26.005,
    "powerTimeInZone_7": 8.999,
    "longestPoolApneaInterval": 0,
    "avgForce": 0,
    "maxForce": 0,
    "normalizedForce": 0,
    "poolApneaBreathHoldDuration": 0,
    "deviceDisplayUnitsDTO": {
      "distanceDisplayMeasure": "string",
      "elevationDisplayMeasure": "string",
      "speedDisplayMeasure": "string",
      "verticalSpeedDisplayMeasure": "string"
    },
    "endTimeGMT": "2026-08-31 22:41:22",
    "qualifyingDive": true,
    "multiDayActivityUUIDs": [
      "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    ],
    "activityUUID": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "carbonOffset": 0,
    "packWeightCalories": 0,
    "standingTime": 0,
    "seatedTime": 0,
    "maxStandingPower": 0,
    "maxSeatedPower": 0,
    "avgStandingPower": 0,
    "avgSeatedPower": 0,
    "parent": true,
    "decoDive": true,
    "elevationCorrected": true,
    "pr": true,
    "manualActivity": true,
    "favorite": true,
    "autoCalcCalories": true
  }
]
```

##### 400

Invalid activity type or subtype: unknown key, activityType identifies a subtype instead of a parent type, activitySubType identifies a parent type instead of a subtype, or activitySubType does not belong to the supplied activityType. Invalid bounding box: when all four coordinates are supplied, latitude must be between -90 and 90 degrees and longitude between -180 and 180 degrees, inclusive. The distance between (upperLatitude, rightLongitude) and (lowerLatitude, leftLongitude) exceeds the maximum distance

##### 401

Authentication is missing or invalid.

##### 403

The caller is not authorized to access this endpoint.

##### 500

An unexpected server error occurred.

## biometric-service

### GET `/biometric-service/heartRateZones/v2`

Retrieve the user's heart rate zone configuration.

#### Parameters

```text
generateDefaults
boolean
(query)
Whether to generate default zones when the user has no configured zones.

Default value : true


true
```

#### Responses

##### 200

Successfully retrieved the user's heart rate zone configuration.

Content type: `application/json`

```json
[
  {
    "trainingMethod": "HR_MAX",
    "restingHeartRateUsed": 0,
    "lactateThresholdHeartRateUsed": 0,
    "zone1Floor": 0,
    "zone2Floor": 0,
    "zone3Floor": 0,
    "zone4Floor": 0,
    "zone5Floor": 0,
    "maxHeartRateUsed": 0,
    "restingHrAutoUpdateUsed": true,
    "sport": "DEFAULT"
  }
]
```

## download-service

### GET `/download-service/files/activity/{activityId}`

Download activity file

Download an activity file in its original format.

#### Parameters

```text
activityId *
integer($int64)
(path)
activityId
```

#### Responses

##### default

default response

Content type: `application/x-zip-compressed`

## fitnessage-service

### GET `/fitnessage-service/fitnessage/v2/{calendarDate}`

Returns the latest Fitness Age information as of the target calendar date.

#### Parameters

```text
calendarDate *
string($date)
(path)
The target date; Fitness Age information returned will be the latest available as of this date.

1989-10-01
fullHistoryScan
boolean
(query)
Whether to scan the full history to find the latest Fitness Age information. If false, only the last 28 days relative to the target calendar date will be considered.

Default value : true


true
```

#### Responses

##### 200

success

Content type: `application/json`

```json
[
  {
    "chronologicalAge": 0,
    "fitnessAge": 0,
    "achievableFitnessAge": 0,
    "previousFitnessAge": 0,
    "components": {
      "additionalProp1": {
        "value": 0,
        "targetValue": 0,
        "improvementValue": 0,
        "potentialAge": 0,
        "priority": 0,
        "stale": true,
        "staleInputs": [
          "string"
        ],
        "lastMeasurementDate": "string",
        "numOfWeeksForIm": 0
      },
      "additionalProp2": {
        "value": 0,
        "targetValue": 0,
        "improvementValue": 0,
        "potentialAge": 0,
        "priority": 0,
        "stale": true,
        "staleInputs": [
          "string"
        ],
        "lastMeasurementDate": "string",
        "numOfWeeksForIm": 0
      },
      "additionalProp3": {
        "value": 0,
        "targetValue": 0,
        "improvementValue": 0,
        "potentialAge": 0,
        "priority": 0,
        "stale": true,
        "staleInputs": [
          "string"
        ],
        "lastMeasurementDate": "string",
        "numOfWeeksForIm": 0
      }
    },
    "lastUpdated": "string",
    "invalidReason": "USER_EMPTY_AGE"
  }
]
```

## goal-service

### GET `/goal-service/goal/user/effective/weightgoal/{startDate}/{endDate}`

Get effective weight goals

Returns the authenticated user's effective weight goals and weight goal ranges for the requested date interval.

#### Parameters

```text
startDate *
string($date)
(path)
Beginning of the requested date interval.

1989-10-01
endDate *
string($date)
(path)
End of the requested date interval.

1989-10-01
```

#### Responses

##### 200

Successfully retrieved effective weight goals for the requested date interval.

Content type: `application/json`

```json
{
  "userGoals": [
    {
      "userGoalCategory": "MY_AUTO",
      "userGoalType": "WEIGHT_GRAMS",
      "startDate": {
        "date": "2026-10-22T18:24:56.072Z",
        "localDate": "2026-10-22"
      },
      "endDate": {
        "date": "2026-10-22T18:24:56.072Z",
        "localDate": "2026-10-22"
      },
      "goalName": "string",
      "goalValue": 0,
      "updateDate": {
        "date": "2026-10-22T18:24:56.072Z",
        "localDate": "2026-10-22"
      },
      "createDate": {
        "date": "2026-10-22T18:24:56.072Z",
        "localDate": "2026-10-22"
      },
      "trackingPeriodType": "SEVEN_DAYS"
    }
  ],
  "userGoalRanges": [
    {
      "userGoalCategory": "MY_AUTO",
      "userGoalType": "WEIGHT_GRAMS",
      "startDate": {
        "date": "2026-10-22T18:24:56.072Z",
        "localDate": "2026-10-22"
      },
      "endDate": {
        "date": "2026-10-22T18:24:56.072Z",
        "localDate": "2026-10-22"
      },
      "lowWeightGoalInGrams": 0,
      "highWeightGoalInGrams": 0,
      "weekNum": 0,
      "trackingPeriodType": "SEVEN_DAYS"
    }
  ]
}
```

##### 400

The date parameters are missing, malformed, or invalid.

##### 401

Authentication is missing or invalid.

##### 403

The authenticated user is not permitted to access this resource.

##### 500

An unexpected server error occurred while retrieving weight goals.

## hrv-service

### GET `/hrv-service/hrv/{calendarDate}`

Get HRV data for a specific date

#### Parameters

```text
calendarDate *
string($date)
(path)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "userProfilePk": 0,
  "hrvSummary": {
    "calendarDate": "string",
    "weeklyAvg": 0,
    "lastNightAvg": 0,
    "lastNight5MinHigh": 0,
    "baseline": {
      "lowUpper": 0,
      "balancedLow": 0,
      "balancedUpper": 0,
      "markerValue": 0
    },
    "status": "NONE",
    "feedbackPhrase": "NONE",
    "createTimeStamp": "string"
  },
  "hrvReadings": [
    {
      "hrvValue": 0,
      "readingTimeGMT": "string",
      "readingTimeLocal": "string"
    }
  ],
  "startTimestampGMT": "string",
  "endTimestampGMT": "string",
  "startTimestampLocal": "string",
  "endTimestampLocal": "string",
  "sleepStartTimestampGMT": "string",
  "sleepEndTimestampGMT": "string",
  "sleepStartTimestampLocal": "string",
  "sleepEndTimestampLocal": "string"
}
```

##### 204

No data

### GET `/hrv-service/hrv/daily/{fromDate}/{toDate}`

Get HRV daily summaries for a date range

#### Parameters

```text
fromDate *
string($date)
(path)
1989-10-01
toDate *
string($date)
(path)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "hrvSummaries": [
    {
      "calendarDate": "string",
      "weeklyAvg": 0,
      "lastNightAvg": 0,
      "lastNight5MinHigh": 0,
      "baseline": {
        "lowUpper": 0,
        "balancedLow": 0,
        "balancedUpper": 0,
        "markerValue": 0
      },
      "status": "NONE",
      "feedbackPhrase": "NONE",
      "createTimeStamp": "string"
    }
  ],
  "userProfilePk": 0
}
```

##### 204

no data

## nutrition-service

### GET `/nutrition-service/food/logs/{date}`

Retrieves the user's daily nutrition summary for a specific calendar date. This includes the user's nutrition goals, nutrients consumed, and discrete events for the day. The response can optionally include meal-by-meal breakdowns of calories and other nutrients consumed by the user on the given date.

#### Parameters

```text
includeGoals
boolean
(query)
Goals are included by default unless requested with includeGoals=false

Default value : true


true
includeNutrition
boolean
(query)
Nutrition information is included by default unless requested with includeNutrition=false

Default value : true


true
includeMedia
boolean
(query)
Images is included by default unless requested with includeMedia=false

Default value : true


true
mealId
integer($int64)
(query)
Id of the meal like id for Breakfast, Lunch, Snacks or Dinner

2
date *
string($date)
(path)
Date for which to retrieve the daily nutrition logs. Date must be in the YYYY-MM-DD format. The date is interpreted in the user's local timezone.

1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "dailyNutritionContent": {
    "calories": 2000,
    "caloriesPercentage": 0,
    "carbs": 275,
    "protein": 0,
    "fat": 0
  },
  "dailyNutritionGoals": {
    "adjustedCalories": 0,
    "adjustedCarbs": 0,
    "adjustedFat": 0,
    "adjustedProtein": 0,
    "calories": 0,
    "carbs": 0,
    "fat": 0,
    "protein": 0
  },
  "dayEndTime": "18:59",
  "dayStartTime": "18:59",
  "loggedFoodsWithServingSizes": [
    {
      "foodImages": [
        {
          "imageType": "0",
          "imageUrl": "https://www.foodimagedb.com/food-images/uuid_1024x1024.png"
        }
      ],
      "foodMetaData": {
        "brandName": "Nestle",
        "customFoodType": "FOOD",
        "foodId": "5642356",
        "foodName": "Toast with Eggs",
        "foodType": "GENERIC",
        "imageUuid": "123e4567-e89b-12d3-a456-426614174000",
        "languageCode": "EN",
        "regionCode": "US",
        "source": "Garmin or FatSecret"
      },
      "isFavorite": true,
      "nutritionContents": [
        {
          "addedSugars": 50,
          "calcium": 1.3,
          "calories": 2000,
          "carbs": 275,
          "cholesterol": 63,
          "fat": 78,
          "fiber": 28,
          "iron": 0.018,
          "monounsaturatedFat": 22,
          "numberOfUnits": 2,
          "polyunsaturatedFat": 16,
          "potassium": 47,
          "protein": 50,
          "saturatedFat": 20,
          "servingId": "34534",
          "servingUnit": "piece or g or cup",
          "sodium": 2.3,
          "sugar": 50,
          "transFat": 2,
          "unitHasServing": true,
          "vitaminA": 62,
          "vitaminC": 0.09,
          "vitaminD": 3
        }
      ]
    }
  ],
  "mealDate": "2025-04-14",
  "mealDetails": [
    {
      "loggedFoods": [
        {
          "customMealId": 12345,
          "foodImages": [
            {
              "imageType": "0",
              "imageUrl": "https://www.foodimagedb.com/food-images/uuid_1024x1024.png"
            }
          ],
          "foodInactive": true,
          "foodMetaData": {
            "brandName": "Nestle",
            "customFoodType": "FOOD",
            "foodId": "5642356",
            "foodName": "Toast with Eggs",
            "foodType": "GENERIC",
            "imageUuid": "123e4567-e89b-12d3-a456-426614174000",
            "languageCode": "EN",
            "regionCode": "US",
            "source": "Garmin or FatSecret"
          },
          "id": "12e1d7c0-f79f-458a-91ba-dec2dd35ede1",
          "isFavorite": true,
          "logCategory": "REGULAR_LOG",
          "logId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "logSource": "GCM or GCW or DEVICE",
          "logTimestamp": "2023-08-01T08:00:00Z",
          "mealDateTimeWithOffset": "2023-08-01T08:00:00-07:00",
          "mealId": 0,
          "mealTime": "08:00:00",
          "nutritionContent": {
            "addedSugars": 50,
            "calcium": 1.3,
            "calories": 2000,
            "carbs": 275,
            "cholesterol": 63,
            "fat": 78,
            "fiber": 28,
            "iron": 0.018,
            "monounsaturatedFat": 22,
            "numberOfUnits": 2,
            "polyunsaturatedFat": 16,
            "potassium": 47,
            "protein": 50,
            "saturatedFat": 20,
            "servingId": "34534",
            "servingUnit": "piece or g or cup",
            "sodium": 2.3,
            "sugar": 50,
            "transFat": 2,
            "unitHasServing": true,
            "vitaminA": 62,
            "vitaminC": 0.09,
            "vitaminD": 3
          },
          "servingQty": 1.6,
          "type": "FOOD"
        }
      ],
      "meal": {
        "defaultMealName": "BREAKFAST",
        "displayOrder": 2,
        "endTime": "18:59",
        "goals": {
          "adjustedCalories": 0,
          "adjustedCarbs": 0,
          "adjustedFat": 0,
          "adjustedProtein": 0,
          "calories": 0,
          "carbs": 0,
          "fat": 0,
          "protein": 0
        },
        "mealId": 12345,
        "mealIndex": 2,
        "mealName": "Lunch",
        "startTime": "18:59",
        "translated": true
      },
      "mealNutritionContent": {
        "calories": 2000,
        "caloriesPercentage": 0,
        "carbs": 275,
        "protein": 0,
        "fat": 0
      },
      "mealNutritionGoals": {
        "adjustedCalories": 0,
        "adjustedCarbs": 0,
        "adjustedFat": 0,
        "adjustedProtein": 0,
        "calories": 0,
        "carbs": 0,
        "fat": 0,
        "protein": 0
      }
    }
  ]
}
```

## periodichealth-service

### GET `/periodichealth-service/menstrualcycle/summary/{calendarDate}`

Get menstrual cycle summary for a date

Returns a summary of the user's menstrual cycle.

#### Parameters

```text
calendarDate *
string($date)
(path)
The calendar date (yyyy-MM-dd) to retrieve data for.

1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "analysis": {
    "cycleTypeAnalysis": {
      "cycleLengthDeviationDays": 0,
      "cycleStartDate": {
        "date": "2026-10-22T18:24:56.085Z",
        "localDate": "2026-10-22"
      },
      "cycleType": "string",
      "cycleVariability": 0,
      "cycleVariabilityClassifier": "string",
      "follicularLengthDeviationDays": 0,
      "hasAmenorrhea": true,
      "isAtypical": true,
      "lutealLengthDeviationDays": 0,
      "medianCycleLength": 0,
      "medianCycleLengthClassifier": "string",
      "periodLengthDeviationDays": 0,
      "prolongedPeriods": 0,
      "prolongedPeriodsClassifier": "string"
    },
    "perimenopauseDetected": true
  },
  "currentPhase": 0,
  "cycleType": "string",
  "dayInCycle": 0,
  "daysUntilNextPhase": 0,
  "deliveryDate": {
    "date": "2026-10-22T18:24:56.085Z",
    "localDate": "2026-10-22"
  },
  "dueDate": {
    "date": "2026-10-22T18:24:56.085Z",
    "localDate": "2026-10-22"
  },
  "educationContentMod": 0,
  "endDate": {
    "date": "2026-10-22T18:24:56.085Z",
    "localDate": "2026-10-22"
  },
  "feedbackPhrase": "string",
  "fertileWindowStart": 0,
  "isSkinTempMct": true,
  "lengthOfCurrentPhase": 0,
  "lengthOfFertileWindow": 0,
  "lutealPhaseStart": 0,
  "numberOfWeek": 0,
  "overlapCycleList": [
    {
      "periodLength": 0,
      "startDate": {
        "date": "2026-10-22T18:24:56.085Z",
        "localDate": "2026-10-22"
      }
    }
  ],
  "periodLength": 0,
  "predictedCycle": true,
  "predictedCycleLength": 0,
  "predictedOvulationDate": {
    "date": "2026-10-22T18:24:56.085Z",
    "localDate": "2026-10-22"
  },
  "pregnancyCycle": true,
  "startDate": {
    "date": "2026-10-22T18:24:56.085Z",
    "localDate": "2026-10-22"
  }
}
```

##### 400

The date parameter is missing, malformed, or invalid.

##### 401

Authentication is missing or invalid.

##### 403

The authenticated user is not permitted to access this resource.

##### 500

An unexpected server error occurred while retrieving Menstrual Cycle summary data.

### GET `/periodichealth-service/menstrualcycle/dayview/{calendarDate}`

Get detailed menstrual cycle day view

Returns detailed menstrual cycle information for a single calendar day, combining the user's logged daily data (symptoms, flow, mood, etc.), the cycle summary for that day, and (for pregnancy tracking) weekly weight goal ranges.

#### Parameters

```text
calendarDate *
string($date)
(path)
The calendar date (yyyy-MM-dd) to retrieve data for.

1989-10-01
todayDate
string($date)
(query)
The current calendar date (yyyy-MM-dd) from the caller's perspective, used as a reference point for predictions and calculations.

1989-10-01
reducedResponse
boolean
(query)
When true, returns a reduced/lightweight version of the response payload.

Default value : false


false
skipbm
boolean
(query)
When true, excludes baby movement (kick count) data from the response.

Default value : false


false
includeAnalysis
boolean
(query)
When true, includes menstrual cycle analysis data in the response.

Default value : false


false
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "dayLog": {
    "babyMovements": [
      {
        "count": 0,
        "duration": 0,
        "movementType": "string",
        "startTimestamp": {
          "date": "2026-10-22T18:24:56.090Z",
          "localDate": "2026-10-22"
        }
      }
    ],
    "calendarDate": {
      "date": "2026-10-22T18:24:56.090Z",
      "localDate": "2026-10-22"
    },
    "discharge": [
      "string"
    ],
    "flow": "string",
    "hasBabyMovement": true,
    "hasGlucoseLog": true,
    "moods": [
      "string"
    ],
    "notes": "string",
    "ovulationDay": true,
    "reportTimestamp": {
      "date": "2026-10-22T18:24:56.090Z",
      "localDate": "2026-10-22"
    },
    "sexDrive": "string",
    "sexualActivity": "string",
    "symptoms": [
      "string"
    ],
    "userProfilePk": 0
  },
  "daySummary": {
    "analysis": {
      "cycleTypeAnalysis": {
        "cycleLengthDeviationDays": 0,
        "cycleStartDate": {
          "date": "2026-10-22T18:24:56.090Z",
          "localDate": "2026-10-22"
        },
        "cycleType": "string",
        "cycleVariability": 0,
        "cycleVariabilityClassifier": "string",
        "follicularLengthDeviationDays": 0,
        "hasAmenorrhea": true,
        "isAtypical": true,
        "lutealLengthDeviationDays": 0,
        "medianCycleLength": 0,
        "medianCycleLengthClassifier": "string",
        "periodLengthDeviationDays": 0,
        "prolongedPeriods": 0,
        "prolongedPeriodsClassifier": "string"
      },
      "perimenopauseDetected": true
    },
    "currentPhase": 0,
    "cycleType": "string",
    "dayInCycle": 0,
    "daysUntilNextPhase": 0,
    "deliveryDate": {
      "date": "2026-10-22T18:24:56.090Z",
      "localDate": "2026-10-22"
    },
    "dueDate": {
      "date": "2026-10-22T18:24:56.090Z",
      "localDate": "2026-10-22"
    },
    "educationContentMod": 0,
    "endDate": {
      "date": "2026-10-22T18:24:56.090Z",
      "localDate": "2026-10-22"
    },
    "feedbackPhrase": "string",
    "fertileWindowStart": 0,
    "isSkinTempMct": true,
    "lengthOfCurrentPhase": 0,
    "lengthOfFertileWindow": 0,
    "lutealPhaseStart": 0,
    "numberOfWeek": 0,
    "overlapCycleList": [
      {
        "periodLength": 0,
        "startDate": {
          "date": "2026-10-22T18:24:56.090Z",
          "localDate": "2026-10-22"
        }
      }
    ],
    "periodLength": 0,
    "predictedCycle": true,
    "predictedCycleLength": 0,
    "predictedOvulationDate": {
      "date": "2026-10-22T18:24:56.090Z",
      "localDate": "2026-10-22"
    },
    "pregnancyCycle": true,
    "startDate": {
      "date": "2026-10-22T18:24:56.090Z",
      "localDate": "2026-10-22"
    }
  },
  "weightGoals": {
    "highWeightGoalInGrams": 0,
    "lowWeightGoalInGrams": 0,
    "weekNum": 0
  }
}
```

##### 400

The date parameters are missing, malformed, or invalid.

##### 401

Authentication is missing or invalid.

##### 403

The authenticated user is not permitted to access this resource.

##### 500

An unexpected server error occurred while retrieving Menstrual Cycle data.

## sleep-service

### GET `/sleep-service/sleep/dailySleep`

Retrieves daily sleep data for a calendar date

#### Parameters

```text
date
string($date)
(query)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "id": 0,
  "userProfilePK": 0,
  "calendarDate": "string",
  "sleepTimeSeconds": 0,
  "napTimeSeconds": 0,
  "sleepWindowConfirmed": true,
  "sleepWindowConfirmationType": "string",
  "sleepStartTimestampGMT": "2026-10-22T18:24:56.094Z",
  "sleepEndTimestampGMT": "2026-10-22T18:24:56.094Z",
  "sleepStartTimestampLocal": "2026-10-22T18:24:56.094Z",
  "sleepEndTimestampLocal": "2026-10-22T18:24:56.094Z",
  "autoSleepStartTimestampGMT": "2026-10-22T18:24:56.094Z",
  "autoSleepEndTimestampGMT": "2026-10-22T18:24:56.094Z",
  "sleepQualityTypePK": "string",
  "sleepResultTypePK": "string",
  "unmeasurableSleepSeconds": 0,
  "deepSleepSeconds": 0,
  "lightSleepSeconds": 0,
  "remSleepSeconds": 0,
  "awakeSleepSeconds": 0,
  "deviceRemCapable": true,
  "sleepFromDevice": true,
  "averageSpO2Value": 0,
  "lowestSpO2Value": 0,
  "highestSpO2Value": 0,
  "numberOfEventsBelowThreshold": 0,
  "averageSpO2HRSleep": 0,
  "spo2Threshold": 0,
  "averageRespirationValue": 0,
  "lowestRespirationValue": 0,
  "highestRespirationValue": 0,
  "awakeCount": 0,
  "avgSleepStress": 0,
  "ageGroup": "TEEN",
  "avgHeartRate": 0,
  "sleepScoreFeedback": "NONE",
  "sleepScoreInsight": "NONE",
  "sleepScorePersonalizedInsight": "NOT_AVAILABLE",
  "sleepScores": {
    "additionalProp1": {
      "value": 0,
      "qualifierKey": "string",
      "optimalStart": 0,
      "optimalEnd": 0,
      "idealStartInSeconds": 0,
      "idealEndInSeconds": 0
    },
    "additionalProp2": {
      "value": 0,
      "qualifierKey": "string",
      "optimalStart": 0,
      "optimalEnd": 0,
      "idealStartInSeconds": 0,
      "idealEndInSeconds": 0
    },
    "additionalProp3": {
      "value": 0,
      "qualifierKey": "string",
      "optimalStart": 0,
      "optimalEnd": 0,
      "idealStartInSeconds": 0,
      "idealEndInSeconds": 0
    }
  },
  "userNote": "string",
  "kidSleepNote": "string",
  "sleepVersion": 0,
  "sleepNeed": {
    "userProfilePk": 0,
    "calendarDate": "2026-10-22",
    "deviceId": 0,
    "timestampGmt": "2026-10-22T18:24:56.094Z",
    "baseline": 0,
    "actual": 0,
    "feedback": "string",
    "trainingFeedback": "string",
    "sleepHistoryAdjustment": "string",
    "hrvAdjustment": "string",
    "napAdjustment": "string",
    "displayedForTheDay": true,
    "recommendedBedtimeStartMins": 0,
    "recommendedBedtimeEndMins": 0,
    "preferredActivityTracker": true
  },
  "nextSleepNeed": {
    "userProfilePk": 0,
    "calendarDate": "2026-10-22",
    "deviceId": 0,
    "timestampGmt": "2026-10-22T18:24:56.094Z",
    "baseline": 0,
    "actual": 0,
    "feedback": "string",
    "trainingFeedback": "string",
    "sleepHistoryAdjustment": "string",
    "hrvAdjustment": "string",
    "napAdjustment": "string",
    "displayedForTheDay": true,
    "recommendedBedtimeStartMins": 0,
    "recommendedBedtimeEndMins": 0,
    "preferredActivityTracker": true
  },
  "dailyNapDTOS": [
    {
      "userProfilePK": 0,
      "deviceId": 0,
      "calendarDate": "2026-10-22",
      "napTimeSec": 0,
      "napStartTimestampGMT": "2026-10-22T18:24:56.094Z",
      "napEndTimestampGMT": "2026-10-22T18:24:56.094Z",
      "napFeedback": "string",
      "napSource": 0,
      "napStartTimeOffset": 0,
      "napEndTimeOffset": 0,
      "createTimestampGMT": "2026-10-22T18:24:56.094Z",
      "updateTimestampGMT": "2026-10-22T18:24:56.094Z"
    }
  ],
  "breathingDisruptionSeverity": "string",
  "sleepAlignment": {
    "userId": 0,
    "calendarDate": "2026-10-22",
    "deviceId": 0,
    "isPreferredActivityTracker": true,
    "sleepNeedBaselineMins": 0,
    "optimalSleepWindowStartMins": 0,
    "optimalSleepWindowEndMins": 0,
    "status": "string",
    "optimalSleepWindowMidpointMins": 0,
    "lastSleepMidpointMins": 0
  }
}
```

### GET `/sleep-service/sleep/dailySleepSummariesByDate`

Retrieves daily sleep summaries data for a date range, up to a maximum of 31 days.

#### Parameters

```text
startDate
string($date)
(query)
1989-10-01
endDate
string($date)
(query)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
[
  {
    "id": 0,
    "userProfilePK": 0,
    "calendarDate": "string",
    "sleepTimeSeconds": 0,
    "napTimeSeconds": 0,
    "sleepWindowConfirmed": true,
    "sleepWindowConfirmationType": "string",
    "sleepStartTimestampGMT": "2026-10-22T18:24:56.101Z",
    "sleepEndTimestampGMT": "2026-10-22T18:24:56.101Z",
    "sleepStartTimestampLocal": "2026-10-22T18:24:56.101Z",
    "sleepEndTimestampLocal": "2026-10-22T18:24:56.101Z",
    "autoSleepStartTimestampGMT": "2026-10-22T18:24:56.101Z",
    "autoSleepEndTimestampGMT": "2026-10-22T18:24:56.101Z",
    "sleepQualityTypePK": "string",
    "sleepResultTypePK": "string",
    "unmeasurableSleepSeconds": 0,
    "deepSleepSeconds": 0,
    "lightSleepSeconds": 0,
    "remSleepSeconds": 0,
    "awakeSleepSeconds": 0,
    "deviceRemCapable": true,
    "sleepFromDevice": true,
    "averageSpO2Value": 0,
    "lowestSpO2Value": 0,
    "highestSpO2Value": 0,
    "numberOfEventsBelowThreshold": 0,
    "averageSpO2HRSleep": 0,
    "spo2Threshold": 0,
    "averageRespirationValue": 0,
    "lowestRespirationValue": 0,
    "highestRespirationValue": 0,
    "awakeCount": 0,
    "avgSleepStress": 0,
    "ageGroup": "TEEN",
    "avgHeartRate": 0,
    "sleepScoreFeedback": "NONE",
    "sleepScoreInsight": "NONE",
    "sleepScorePersonalizedInsight": "NOT_AVAILABLE",
    "sleepScores": {
      "additionalProp1": {
        "value": 0,
        "qualifierKey": "string",
        "optimalStart": 0,
        "optimalEnd": 0,
        "idealStartInSeconds": 0,
        "idealEndInSeconds": 0
      },
      "additionalProp2": {
        "value": 0,
        "qualifierKey": "string",
        "optimalStart": 0,
        "optimalEnd": 0,
        "idealStartInSeconds": 0,
        "idealEndInSeconds": 0
      },
      "additionalProp3": {
        "value": 0,
        "qualifierKey": "string",
        "optimalStart": 0,
        "optimalEnd": 0,
        "idealStartInSeconds": 0,
        "idealEndInSeconds": 0
      }
    },
    "userNote": "string",
    "kidSleepNote": "string",
    "sleepVersion": 0,
    "sleepNeed": {
      "userProfilePk": 0,
      "calendarDate": "2026-10-22",
      "deviceId": 0,
      "timestampGmt": "2026-10-22T18:24:56.101Z",
      "baseline": 0,
      "actual": 0,
      "feedback": "string",
      "trainingFeedback": "string",
      "sleepHistoryAdjustment": "string",
      "hrvAdjustment": "string",
      "napAdjustment": "string",
      "displayedForTheDay": true,
      "recommendedBedtimeStartMins": 0,
      "recommendedBedtimeEndMins": 0,
      "preferredActivityTracker": true
    },
    "nextSleepNeed": {
      "userProfilePk": 0,
      "calendarDate": "2026-10-22",
      "deviceId": 0,
      "timestampGmt": "2026-10-22T18:24:56.101Z",
      "baseline": 0,
      "actual": 0,
      "feedback": "string",
      "trainingFeedback": "string",
      "sleepHistoryAdjustment": "string",
      "hrvAdjustment": "string",
      "napAdjustment": "string",
      "displayedForTheDay": true,
      "recommendedBedtimeStartMins": 0,
      "recommendedBedtimeEndMins": 0,
      "preferredActivityTracker": true
    },
    "dailyNapDTOS": [
      {
        "userProfilePK": 0,
        "deviceId": 0,
        "calendarDate": "2026-10-22",
        "napTimeSec": 0,
        "napStartTimestampGMT": "2026-10-22T18:24:56.101Z",
        "napEndTimestampGMT": "2026-10-22T18:24:56.101Z",
        "napFeedback": "string",
        "napSource": 0,
        "napStartTimeOffset": 0,
        "napEndTimeOffset": 0,
        "createTimestampGMT": "2026-10-22T18:24:56.101Z",
        "updateTimestampGMT": "2026-10-22T18:24:56.101Z"
      }
    ],
    "breathingDisruptionSeverity": "string",
    "sleepAlignment": {
      "userId": 0,
      "calendarDate": "2026-10-22",
      "deviceId": 0,
      "isPreferredActivityTracker": true,
      "sleepNeedBaselineMins": 0,
      "optimalSleepWindowStartMins": 0,
      "optimalSleepWindowEndMins": 0,
      "status": "string",
      "optimalSleepWindowMidpointMins": 0,
      "lastSleepMidpointMins": 0
    }
  }
]
```

## userprofile-service

### GET `/userprofile-service/userprofile/settings`

Retrieve the user profile settings.

#### Parameters

```text
No parameters
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "displayName": "string",
  "preferredLocale": "en, fr, it",
  "measurementSystem": "metric, statute_us, statute_uk",
  "firstDayOfWeek": {
    "dayId": 0,
    "dayName": "monday, tuesday, wednesday, thursday, friday, saturday, sunday",
    "sortOrder": 0,
    "isPossibleFirstDay": true
  },
  "numberFormat": "decimal_period, decimal_comma",
  "timeFormat": {
    "formatId": 0,
    "formatKey": "string",
    "minFraction": 0,
    "maxFraction": 0,
    "groupingUsed": true,
    "displayFormat": "string"
  },
  "dateFormat": {
    "formatId": 0,
    "formatKey": "string",
    "minFraction": 0,
    "maxFraction": 0,
    "groupingUsed": true,
    "displayFormat": "string"
  },
  "powerFormat": {
    "formatId": 0,
    "formatKey": "string",
    "minFraction": 0,
    "maxFraction": 0,
    "groupingUsed": true,
    "displayFormat": "string"
  },
  "heartRateFormat": {
    "formatId": 0,
    "formatKey": "string",
    "minFraction": 0,
    "maxFraction": 0,
    "groupingUsed": true,
    "displayFormat": "string"
  },
  "timeZone": "gmt, America/Chicago, Atlantic/South_Georgia",
  "hydrationMeasurementUnit": "cup, milliliter",
  "hydrationContainers": [
    {
      "name": "string",
      "volume": 0,
      "unit": "string"
    }
  ],
  "glucoseMeasurementUnit": "millimolesPerLitre, milligramsPerDecilitre",
  "golfDistanceUnit": "metric, statute_us, statute_uk",
  "golfElevationUnit": "string",
  "golfSpeedUnit": "string",
  "wheelchairModeEnabled": true,
  "availableTrainingDays": [
    "MONDAY"
  ],
  "preferredLongTrainingDays": [
    "MONDAY"
  ]
}
```

## usersummary-service

### GET `/usersummary-service/stats/hydration/daily/{startDate}/{endDate}`

Get daily hydration data for a date range, up to a maximum of 31 days.

#### Parameters

```text
startDate *
string($date)
(path)
1989-10-01
endDate *
string($date)
(path)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
[
  {
    "userId": 0,
    "calendarDate": "2026-10-22",
    "valueInML": 0,
    "goalInML": 0,
    "lastEntryTimestampLocal": "2026-10-22T18:24:56.111Z",
    "sweatLossInML": 0,
    "activityIntakeInML": 0
  }
]
```

### GET `/usersummary-service/stats/steps/daily/{startDate}/{endDate}`

Get daily steps data for a date range, up to a maximum of 28 days.

#### Parameters

```text
startDate *
string($date)
(path)
1989-10-01
endDate *
string($date)
(path)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
[
  {
    "calendarDate": "2026-10-22",
    "totalSteps": 0,
    "totalDistance": 0,
    "stepGoal": 0
  }
]
```

### GET `/usersummary-service/stats/stress/daily/{startDate}/{endDate}`

Get daily stress data for a date range, up to a maximum of 28 days.

#### Parameters

```text
startDate *
string($date)
(path)
1989-10-01
endDate *
string($date)
(path)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
[
  {
    "calendarDate": "2026-10-22",
    "values": {
      "additionalProp1": 0,
      "additionalProp2": 0,
      "additionalProp3": 0
    }
  }
]
```

### GET `/usersummary-service/usersummary/daily`

Get user summary data for a specific date. User summary data includes steps, calories, stress, Body Battery, and other wellness metrics for the given date.

#### Parameters

```text
calendarDate
string($date)
(query)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "userProfileId": 0,
  "displayName": "string",
  "totalKilocalories": 0,
  "activeKilocalories": 0,
  "bmrKilocalories": 0,
  "consumedKilocalories": 0,
  "remainingKilocalories": 0,
  "totalSteps": 0,
  "netCalorieGoal": 0,
  "totalDistanceMeters": 0,
  "wellnessDistanceMeters": 0,
  "userDailySummaryId": 0,
  "calendarDate": "2026-10-22",
  "uuid": "string",
  "dailyStepGoal": 0,
  "dailyPushesGoal": 0,
  "totalPushDistance": 0,
  "totalPushes": 0,
  "wellnessStartTimeGmt": "2026-10-22T18:24:56.117Z",
  "wellnessStartTimeLocal": "2026-10-22T18:24:56.117Z",
  "wellnessEndTimeGmt": "2026-10-22T18:24:56.117Z",
  "wellnessEndTimeLocal": "2026-10-22T18:24:56.117Z",
  "durationInMilliseconds": 0,
  "wellnessDescription": "string",
  "highlyActiveSeconds": 0,
  "activeSeconds": 0,
  "sedentarySeconds": 0,
  "sleepingSeconds": 0,
  "includesWellnessData": true,
  "includesActivityData": true,
  "includesCalorieConsumedData": true,
  "moderateIntensityMinutes": 0,
  "vigorousIntensityMinutes": 0,
  "floorsAscendedInMeters": 0,
  "floorsDescendedInMeters": 0,
  "floorsAscended": 0,
  "floorsDescended": 0,
  "intensityMinutesGoal": 0,
  "userFloorsAscendedGoal": 0,
  "minHeartRate": 0,
  "maxHeartRate": 0,
  "restingHeartRate": 0,
  "lastSevenDaysAvgRestingHeartRate": 0,
  "source": "GARMIN",
  "averageStressLevel": 0,
  "maxStressLevel": 0,
  "stressDuration": 0,
  "restStressDuration": 0,
  "activityStressDuration": 0,
  "uncategorizedStressDuration": 0,
  "totalStressDuration": 0,
  "lowStressDuration": 0,
  "mediumStressDuration": 0,
  "highStressDuration": 0,
  "stressPercentage": 0,
  "restStressPercentage": 0,
  "activityStressPercentage": 0,
  "uncategorizedStressPercentage": 0,
  "lowStressPercentage": 0,
  "mediumStressPercentage": 0,
  "highStressPercentage": 0,
  "stressQualifier": "CALM",
  "measurableAwakeDuration": 0,
  "measurableAsleepDuration": 0,
  "lastSyncTimestampGMT": "2026-10-22T18:24:56.117Z",
  "minAvgHeartRate": 0,
  "maxAvgHeartRate": 0,
  "bodyBatteryChargedValue": 0,
  "bodyBatteryDrainedValue": 0,
  "bodyBatteryHighestValue": 0,
  "bodyBatteryLowestValue": 0,
  "bodyBatteryMostRecentValue": 0,
  "bodyBatteryDuringSleep": 0,
  "bodyBatteryAtWakeTime": 0,
  "bodyBatteryVersion": 0,
  "abnormalHeartRateAlertsCount": 0,
  "averageSpo2": 0,
  "lowestSpo2": 0,
  "latestSpo2": 0,
  "latestSpo2ReadingTimeGmt": "2026-10-22T18:24:56.117Z",
  "latestSpo2ReadingTimeLocal": "2026-10-22T18:24:56.117Z",
  "averageMonitoringEnvironmentAltitude": 0,
  "bodyBatteryDynamicFeedbackEvent": {
    "eventTimestampGmt": "2026-10-22T18:24:56.117Z",
    "bodyBatteryLevel": "string",
    "feedbackShortType": "string",
    "feedbackLongType": "string"
  },
  "endOfDayBodyBatteryDynamicFeedbackEvent": {
    "eventTimestampGmt": "2026-10-22T18:24:56.117Z",
    "bodyBatteryLevel": "string",
    "feedbackShortType": "string",
    "feedbackLongType": "string"
  },
  "bodyBatteryActivityEventList": [
    {
      "eventType": "string",
      "eventStartTimeGmt": "2026-10-22T18:24:56.117Z",
      "timezoneOffset": 0,
      "durationInMilliseconds": 0,
      "bodyBatteryImpact": 0,
      "feedbackType": "string",
      "shortFeedback": "string"
    }
  ],
  "isJetLagDay": true,
  "jetLagTripName": "string",
  "hydrationValueInML": 0,
  "hydrationGoalInML": 0,
  "avgWakingRespirationValue": 0,
  "highestRespirationValue": 0,
  "lowestRespirationValue": 0,
  "latestRespirationValue": 0,
  "latestRespirationTimeGMT": "2026-10-22T18:24:56.117Z",
  "respirationAlgorithmVersion": 0
}
```

### GET `/usersummary-service/v2/dailysummaries`

Get user daily summaries for a date range, up to a maximum of 1 year.

#### Parameters

```text
startDate
string($date)
(query)
1989-10-01
endDate
string($date)
(query)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "data": [
    {
      "uuid": "123e4567-e89b-12d3-a456-426655440000",
      "userProfilePk": 987654321,
      "calendarDate": "2023-10-09",
      "source": "garmin",
      "includesWellnessData": true,
      "includesActivityData": true,
      "wellnessChronology": {
        "startTimestampGmt": "2026-10-22T18:24:56.122Z",
        "startTimestampLocal": "2026-10-22T18:24:56.122Z",
        "endTimestampGmt": "2026-10-22T18:24:56.122Z",
        "endTimestampLocal": "2026-10-22T18:24:56.122Z",
        "totalDurationInMillis": 57600000
      },
      "movement": "{\"steps\":{\"goal\":10000,\"value\",5000,\"distanceInMeters\",3810.0},\"pushes\":{\"goal\":2500,\"value\":1250,\"distanceInMeters\":316.8},\"floorsAscended\":{\"goal\":10,\"value\":5,\"distanceInMeters\":15.24},\"floorsDescended\":{\"value\":3,\"distanceInMeters\":9.144}}",
      "calories": {
        "burnedResting": 1000,
        "burnedActive": 500,
        "burnedTotal": 1500,
        "consumedGoal": 2000,
        "consumedValue": 1200,
        "consumedRemaining": 1300
      },
      "heartRate": {
        "minValue": 60,
        "maxValue": 180,
        "restingValue": 100,
        "alertCount": 0
      },
      "intensityMinutes": {
        "goal": 150,
        "moderate": 30,
        "vigorous": 15
      },
      "stress": {
        "avgLevel": 50,
        "maxLevel": 100,
        "restProportion": 0.47,
        "activityProportion": 0.06,
        "uncategorizedProportion": 0.03,
        "lowStressProportion": 0.22,
        "mediumStressProportion": 0.19,
        "highStressProportion": 0.03,
        "qualifier": "very_stressful",
        "totalDurationInMillis": 57600000,
        "restDurationInMillis": 27000000,
        "activityDurationInMillis": 3600000,
        "uncategorizedDurationInMillis": 1800000,
        "lowStressDurationInMillis": 12600000,
        "mediumStressDurationInMillis": 10800000,
        "highStressDurationInMillis": 1800000
      },
      "bodyBattery": {
        "minValue": 10,
        "maxValue": 85,
        "chargedValue": 80,
        "drainedValue": 20,
        "latestValue": 60,
        "endOfDayValue": 20,
        "featureVersion": "2.0",
        "dynamicFeedbackEvent": {
          "eventTimestampGmt": "2026-10-22T18:24:56.122Z",
          "bodyBatteryLevel": "string",
          "feedbackShortType": "string",
          "feedbackLongType": "string"
        },
        "endOfDayDynamicFeedbackEvent": {
          "eventTimestampGmt": "2026-10-22T18:24:56.122Z",
          "bodyBatteryLevel": "string",
          "feedbackShortType": "string",
          "feedbackLongType": "string"
        },
        "activityEvents": [
          {
            "eventType": "string",
            "eventStartTimeGmt": "2026-10-22T18:24:56.122Z",
            "eventStartTimeLocal": "2026-10-22T18:24:56.122Z",
            "bodyBatteryImpact": 0,
            "feedbackType": "string",
            "shortFeedback": "string",
            "deviceId": 0,
            "activityName": "string",
            "activityType": "string",
            "activityId": 0,
            "durationInMillis": 3600000
          }
        ]
      },
      "hydration": {
        "goalInMl": 2000,
        "goalInFractionalMl": 2000.4321,
        "consumedInFractionalMl": 1000.4321
      },
      "respiration": {
        "avgValue": 15,
        "maxValue": 20,
        "minValue": 10,
        "latestValue": 18,
        "latestTimestampGmt": "2026-10-22T18:24:56.122Z",
        "algorithmVersion": 100
      },
      "pulseOx": {
        "avgValue": 95,
        "minValue": 90,
        "latestValue": 94,
        "latestTimestampGmt": "2026-10-22T18:24:56.122Z",
        "latestTimestampLocal": "2026-10-22T18:24:56.122Z",
        "avgAltitudeInMeters": 327
      },
      "jetLag": {
        "tripName": "string"
      }
    }
  ]
}
```

## weight-service

### GET `/weight-service/weight/all/{startDate}/{endDate}`

Retrieve all weight entries for a specified date range.

#### Parameters

```text
startDate *
string($date)
(path)
The start date(user's local calendar) of the range, inclusive. Format yyyy-MM-dd.

1989-10-01
endDate *
string($date)
(path)
The end date(user's local calendar) of the range, inclusive. Format yyyy-MM-dd.

1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
[
  {
    "date": "2026-10-22T18:24:56.128Z",
    "calendarDate": "string",
    "weight": 0,
    "bmi": 0,
    "bodyFat": 0,
    "bodyWater": 0,
    "boneMass": 0,
    "muscleMass": 0,
    "physiqueRating": 0,
    "visceralFat": 0,
    "metabolicAge": 0,
    "timestampGMT": "2026-10-22T18:24:56.128Z",
    "weightDelta": 0
  }
]
```

### GET `/weight-service/weight/range/{startDate}/{endDate}`

Retrieve weight summaries for a date range, including daily latest weights, the range average, and adjacent weights.

#### Parameters

```text
startDate *
string($date)
(path)
The start date(user's local calendar) of the range, inclusive. Format yyyy-MM-dd.

1989-10-01
endDate *
string($date)
(path)
The end date(user's local calendar) of the range, inclusive. Format yyyy-MM-dd.

1989-10-01
includeAll
boolean
(query)
If true, include all weight entries for each day in the range. If false, only include the latest weight entry for each day.

Default value : false


false
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "dailyWeightSummaries": [
    {
      "summaryDate": "string",
      "numOfWeightEntries": 0,
      "minWeight": 0,
      "maxWeight": 0,
      "latestWeight": {
        "date": "2026-10-22T18:24:56.131Z",
        "calendarDate": "string",
        "weight": 0,
        "bmi": 0,
        "bodyFat": 0,
        "bodyWater": 0,
        "boneMass": 0,
        "muscleMass": 0,
        "physiqueRating": 0,
        "visceralFat": 0,
        "metabolicAge": 0,
        "timestampGMT": "2026-10-22T18:24:56.131Z",
        "weightDelta": 0
      },
      "allWeightMetrics": [
        {
          "date": "2026-10-22T18:24:56.131Z",
          "calendarDate": "string",
          "weight": 0,
          "bmi": 0,
          "bodyFat": 0,
          "bodyWater": 0,
          "boneMass": 0,
          "muscleMass": 0,
          "physiqueRating": 0,
          "visceralFat": 0,
          "metabolicAge": 0,
          "timestampGMT": "2026-10-22T18:24:56.131Z",
          "weightDelta": 0
        }
      ]
    }
  ],
  "totalAverage": {
    "from": "2026-10-22T18:24:56.131Z",
    "until": "2026-10-22T18:24:56.131Z",
    "weight": 0,
    "bmi": 0,
    "bodyFat": 0,
    "bodyWater": 0,
    "boneMass": 0,
    "muscleMass": 0,
    "physiqueRating": 0,
    "visceralFat": 0,
    "metabolicAge": 0
  },
  "previousDateWeight": {
    "date": "2026-10-22T18:24:56.131Z",
    "calendarDate": "string",
    "weight": 0,
    "bmi": 0,
    "bodyFat": 0,
    "bodyWater": 0,
    "boneMass": 0,
    "muscleMass": 0,
    "physiqueRating": 0,
    "visceralFat": 0,
    "metabolicAge": 0,
    "timestampGMT": "2026-10-22T18:24:56.131Z",
    "weightDelta": 0
  },
  "nextDateWeight": {
    "date": "2026-10-22T18:24:56.131Z",
    "calendarDate": "string",
    "weight": 0,
    "bmi": 0,
    "bodyFat": 0,
    "bodyWater": 0,
    "boneMass": 0,
    "muscleMass": 0,
    "physiqueRating": 0,
    "visceralFat": 0,
    "metabolicAge": 0,
    "timestampGMT": "2026-10-22T18:24:56.131Z",
    "weightDelta": 0
  }
}
```

## wellness-service

### GET `/wellness-service/wellness/bodyBattery/reports/daily`

Returns daily Body Battery reports for a date range, up to a maximum of 31 days.

#### Parameters

```text
startDate
string($date)
(query)
1989-10-01
endDate
string($date)
(query)
1989-10-01
chunks
integer($int32)
(query)
Number of time intervals each day is divided into; the response includes the lowest and highest Body Battery readings from each interval.

chunks
```

#### Responses

##### 200

success

Content type: `application/json`

```json
[
  {
    "date": "2026-10-22",
    "charged": 0,
    "drained": 0,
    "startTimestampGMT": "2026-10-22T18:24:56.136Z",
    "endTimestampGMT": "2026-10-22T18:24:56.136Z",
    "startTimestampLocal": "2026-10-22T18:24:56.136Z",
    "endTimestampLocal": "2026-10-22T18:24:56.136Z",
    "bodyBatteryValuesArray": [
      [
        {}
      ]
    ],
    "bodyBatteryValueDescriptorDTOList": [
      {
        "bodyBatteryValueDescriptorIndex": 0,
        "bodyBatteryValueDescriptorKey": "string"
      }
    ],
    "bodyBatteryDynamicFeedbackEvent": {
      "eventTimestampGmt": "2026-10-22T18:24:56.136Z",
      "bodyBatteryLevel": "string",
      "feedbackShortType": "string",
      "feedbackLongType": "string"
    },
    "bodyBatteryActivityEvent": [
      {
        "eventType": "string",
        "eventStartTimeGmt": "2026-10-22T18:24:56.136Z",
        "timezoneOffset": 0,
        "durationInMilliseconds": 0,
        "bodyBatteryImpact": 0,
        "feedbackType": "string",
        "shortFeedback": "string"
      }
    ],
    "endOfDayBodyBatteryDynamicFeedbackEvent": {
      "eventTimestampGmt": "2026-10-22T18:24:56.136Z",
      "bodyBatteryLevel": "string",
      "feedbackShortType": "string",
      "feedbackLongType": "string"
    }
  }
]
```

##### 400

The date parameters are missing, malformed, or invalid.

##### 401

Authentication is missing or invalid.

##### 403

The authenticated user is not permitted to access this resource.

##### 500

An unexpected server error occurred while retrieving Body Battery data.

### GET `/wellness-service/wellness/daily/spo2acclimation/{calendarDate}`

Returns daily SpO2 readings data for a given calendar date.

#### Parameters

```text
calendarDate *
string($date)
(path)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "userProfilePK": 0,
  "calendarDate": "string",
  "startTimestampGMT": "string",
  "endTimestampGMT": "string",
  "startTimestampLocal": "string",
  "endTimestampLocal": "string",
  "sleepStartTimestampGMT": "string",
  "sleepEndTimestampGMT": "string",
  "sleepStartTimestampLocal": "string",
  "sleepEndTimestampLocal": "string",
  "tomorrowSleepStartTimestampGMT": "string",
  "tomorrowSleepEndTimestampGMT": "string",
  "tomorrowSleepStartTimestampLocal": "string",
  "tomorrowSleepEndTimestampLocal": "string",
  "averageSpO2": 0,
  "lowestSpO2": 0,
  "lastSevenDaysAvgSpO2": 0,
  "latestSpO2": 0,
  "latestSpO2TimestampGMT": "string",
  "latestSpO2TimestampLocal": "string",
  "avgSleepSpO2": 0,
  "avgTomorrowSleepSpO2": 0,
  "spO2SingleValuesDescriptorList": [
    {
      "spo2ValueDescriptorIndex": 0,
      "spo2ValueDescriptorKey": "string"
    }
  ],
  "spO2SingleValues": [
    [
      {}
    ]
  ],
  "spO2HourlyAveragesDescriptorList": [
    {
      "spo2ValueDescIndex": 0,
      "spo2ValueDescKey": "string"
    }
  ],
  "spO2HourlyAverages": [
    [
      {}
    ]
  ],
  "monitoringEnvironmentValuesDescriptorList": [
    {
      "monEnvValueDescIndex": 0,
      "monEnvValueDescKey": "string"
    }
  ],
  "monitoringEnvironmentValues": [
    [
      {}
    ]
  ]
}
```

##### 400

The date parameter is missing, malformed, or invalid.

##### 401

Authentication is missing or invalid.

##### 403

The authenticated user is not permitted to access this resource.

##### 500

An unexpected server error occurred while retrieving SpO2 readings data.

### GET `/wellness-service/wellness/dailyHeartRate`

Returns daily heart rate data for a given date.

#### Parameters

```text
date
string($date)
(query)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
{
  "userProfilePK": 0,
  "calendarDate": {
    "date": "2026-10-22T18:24:56.142Z",
    "localDate": "2026-10-22"
  },
  "startTimestampGMT": {
    "date": "2026-10-22T18:24:56.142Z",
    "localDate": "2026-10-22"
  },
  "endTimestampGMT": {
    "date": "2026-10-22T18:24:56.142Z",
    "localDate": "2026-10-22"
  },
  "startTimestampLocal": {
    "date": "2026-10-22T18:24:56.142Z",
    "localDate": "2026-10-22"
  },
  "endTimestampLocal": {
    "date": "2026-10-22T18:24:56.142Z",
    "localDate": "2026-10-22"
  },
  "maxHeartRate": 0,
  "minHeartRate": 0,
  "restingHeartRate": 0,
  "lastSevenDaysAvgRestingHeartRate": 0,
  "abnormalHrThresholdValue": 0,
  "lowAbnormalHrThresholdValue": 0,
  "abnormalHRValuesArray": [
    [
      {}
    ]
  ],
  "heartRateValueDescriptors": [
    {
      "index": 0,
      "key": "string"
    }
  ],
  "heartRateValues": [
    [
      {}
    ]
  ]
}
```

##### 400

The date parameter is missing, malformed, or invalid.

##### 401

Authentication is missing or invalid.

##### 403

The authenticated user is not permitted to access this resource.

##### 500

An unexpected server error occurred while retrieving Heart rate data.

## wellnessactivity-service

### GET `/wellnessactivity-service/activity/summary/range/{fromDate}/{untilDate}`

Returns a list of wellness activity summaries for the given date range. The fromDate and untilDate are inclusive.

#### Parameters

```text
fromDate *
string($date)
(path)
1989-10-01
untilDate *
string($date)
(path)
1989-10-01
```

#### Responses

##### 200

success

Content type: `application/json`

```json
[
  {
    "userProfilePk": 0,
    "activityUuid": {
      "leastSignificantBits": 0,
      "mostSignificantBits": 0,
      "baseUUID": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    },
    "calendarDate": {
      "date": "2026-10-22T18:24:56.144Z",
      "localDate": "2026-10-22"
    },
    "rulePK": 0,
    "activityName": "string",
    "notes": "string",
    "wellnessActivityType": "UNKNOWN",
    "startTimestampGMT": {
      "date": "2026-10-22T18:24:56.144Z",
      "localDate": "2026-10-22"
    },
    "endTimestampGMT": {
      "date": "2026-10-22T18:24:56.144Z",
      "localDate": "2026-10-22"
    },
    "startTimestampLocal": {
      "date": "2026-10-22T18:24:56.144Z",
      "localDate": "2026-10-22"
    },
    "endTimestampLocal": {
      "date": "2026-10-22T18:24:56.144Z",
      "localDate": "2026-10-22"
    },
    "summaryTypeDataList": [
      {
        "summaryType": "HEART_RATE",
        "minValue": 0,
        "maxValue": 0,
        "avgValue": 0
      }
    ],
    "timeInZoneList": [
      {
        "zoneNumber": 0,
        "millisInZone": 0,
        "zoneLowBoundary": 0
      }
    ],
    "deviceMetaData": {
      "deviceId": 0,
      "deviceTypeId": 0,
      "deviceVersionId": 0,
      "deviceVersion": "string",
      "deviceName": "string"
    }
  }
]
```

##### 400

The date parameters are missing, malformed, or invalid.

##### 401

Authentication is missing or invalid.

##### 403

The authenticated user is not permitted to access this resource.

##### 500

An unexpected server error occurred while retrieving wellness activity summary data.

## Schemas

### ActivitySummaryDTO

```text
ActivitySummaryDTO{
activityId	integer($int64)
Unique identifier of the activity

activityUUID	{...}
activityName	string
Name of the activity

description	string
User provided description of the activity

userProfileId	integer($int64)
Identifier of the user who owns the activity

parentId	integer($int64)
Identifier of the parent activity

parentName	string
The parent name associated with the activity

isMultiSportParent	boolean
Indicates whether this activity is the parent of a multisport activity.

activityTypeDTO	{...}
example: OrderedMap { "typeId": 1, "typeKey": "running", "parentTypeId": 17 }
eventTypeDTO	{...}
accessControlRuleDTO	{...}
timeZoneUnitDTO	{...}
example: OrderedMap { "unitId": 152, "unitKey": "America/Chicago", "timeZone": "America/Chicago" }
metadataDTO	{...}
summaryDTO	{...}
locationName	string
Location name associated with the activity

diveInfo	{...}
splitSummaries	[...]
videoGameInfo	{...}
deviceDisplayUnitsDTO	{...}
}
```

### ActivityTypeDTO

```text
ActivityTypeDTO{
description:
Activity type identifier, key, and reference to its parent activity type

typeId	integer($int64)
Identifier of the activity type

typeKey	string
Key identifying the activity type

parentTypeId	integer($int64)
Reference to the typeId of the parent activity type. A value of 17 means the current activity type is a parent activity type.

}
example: OrderedMap { "typeId": 1, "typeKey": "running", "parentTypeId": 17 }
```

### EventTypeDTO

```text
EventTypeDTO{
typeId	integer($int64)
Identifier of the event classification associated with the activity

typeKey	string
example: race
Key identifying the event classification associated with the activity, such as race, training, recreation, fitness, specialEvent, or uncategorized

}
```

### AccessControlRuleDTO

```text
AccessControlRuleDTO{
description:
Privacy settings controlling who can access the activity

typeId	integer($int64)
Identifier of the activity's privacy setting

typeKey	string
example: private
Key identifying the activity's privacy setting, such as public, private, subscribers, or groups

}
```

### TimeZoneUnitDTO

```text
TimeZoneUnitDTO{
description:
Time zone associated with the activity

unitId	integer($int64)
example: 152
Identifier of the time zone unit

unitKey	string
example: America/Chicago
Key identifying the time zone unit, such as America/Chicago

timeZone	string
example: America/Chicago
The IANA time zone identifier from the activity's local time, such as America/Chicago

}
example: OrderedMap { "unitId": 152, "unitKey": "America/Chicago", "timeZone": "America/Chicago" }
```

### MetadataDTO

```text
MetadataDTO{
isOriginal	boolean
Indicates whether the activity's recorded data has not been edited since it was uploaded. False when activity data has been modified, such as by trimming or manually adjusting recorded data.

fileFormat	ApplicationFormatDTO{...}
example: OrderedMap { "formatId": 7, "formatKey": "fit" }
lastUpdateDate	string
pattern: ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+$
example: 2022-08-10T09:47:59.031
ISO 8601 timestamp in UTC, represented without a GMT offset or trailing 'Z'

uploadedDate	string
pattern: ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+$
example: 2022-08-10T09:47:59.031
ISO 8601 timestamp in UTC, represented without a GMT offset or trailing 'Z'

videoUrl	string
URL of a video uploaded by the user and associated with the activity. Null when no video is associated with the activity.

userInfoDto	UserInfoDto{...}
childIds	[...]
childActivityTypes	[...]
sensors	[...]
activityImages	[...]
manufacturer	string
Manufacturer that produced the uploaded activity file

lapCount	integer($int32)
Total number of laps in the activity, or total number of dives for some apnea dive activities

eBikeMaxAssistModes	integer($int32)
Highest e-bike assist mode observed during the activity

eBikeBatteryUsage	integer($int32)
Total e-bike battery usage for the entire activity, in percentage points

eBikeBatteryRemaining	integer($int32)
E-bike battery level at the end of the activity, as a percentage

eBikeAssistModeInfoDTOList	[...]
hasRunPowerWindData	boolean
Indicates whether wind data was used to determine running power for the activity; null when wind is not enabled for running power on the device.

calendarEventInfo	CalendarEventInfoDTO{...}
isWheelchair	boolean
Indicates whether the activity was performed in wheelchair mode or includes a wheelchair exercise workout.

specializedWorkoutCategories	[...]
hasMultiDayActivities	boolean
Indicates whether the activity is part of an Epic.

personalRecord	boolean
Indicates whether the activity is a personal record.

gcj02	boolean
Indicates whether the activity's coordinates use the GCJ-02 coordinate system, commonly used for mapping in China.

runPowerWindDataEnabled	boolean
Indicates whether the user enabled wind data for running power calculations in the device's training settings.

trimmed	boolean
Indicates whether the activity has been trimmed to remove part of the original recording.

manualActivity	boolean
Indicates whether the activity is identified as manually entered rather than recorded by a device.

elevationCorrected	boolean
Indicates whether corrected elevation data is used for the activity. Set during upload according to device capabilities and the upload's correction setting; users can also toggle it later.

autoCalcCalories	boolean
True when calories were calculated because no calorie measurement was available; the estimate uses activity type, user weight, duration, and distance when available.

favorite	boolean
Indicates whether the user marked their activity as a favorite.

}
```

### ApplicationFormatDTO

```text
ApplicationFormatDTO{
description:
Source file format associated with the activity.

formatId	integer($int64)
Stored file-format identifier: 1 for tcx, 2 for gpx, 3 for deviceXml, 4 for hst, 5 for axm, 6 for kml, or 7 for fit

formatKey	string
example: fit
Name corresponding to formatId, such as tcx, gpx, deviceXml, hst, axm, kml, or fit

}
example: OrderedMap { "formatId": 7, "formatKey": "fit" }
```

### UserInfoDto

```text
UserInfoDto{
userProfilePk	integer($int64)
displayname	string
fullname	string
profileImageUrlLarge	string
profileImageUrlMedium	string
profileImageUrlSmall	string
}
```

### UUID

```text
UUID{
description:
Universally unique identifier

uuid	string
pattern: [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}
}
```

### SensorInfoDTO

```text
SensorInfoDTO{
description:
Information about a sensor or accessory associated with the activity ignoring built-in sensors and the device that recorded the activity.

manufacturer	string
example: GARMIN
Sensor or accessory manufacturer

serialNumber	integer($int64)
example: 30218472
Serial number identifying the sensor or accessory.

sku	string
example: 006-B2900-00
Product SKU or part number for the accessory, when available, such as a Garmin part number or a Tacx product code.

fitProductNumber	integer($int32)
example: 2900
Numeric product identifier from the device information.

sourceType	string
example: ANTPLUS
Communication source, such as ANT, ANTPLUS or BLUETOOTH_LOW_ENERGY

antplusDeviceType	string
example: HEART_RATE
ANT+ device type name, such as HEART_RATE or BIKE_POWER. Applicable to sensors whose sourceType is ANTPLUS.

localDeviceType	string
example: WHR
Built-in device type name, such as WHR for a wrist heart rate sensor. Applicable when sourceType is LOCAL

bodyLocation	string
example: WAIST_MID_BACK
Location of the sensor on the user's body, expressed as a body location name, when known.

softwareVersion	number($float)
example: 1.18
Version of the sensor's internal software, when known.

batteryStatus	string
example: GOOD
Qualitative battery condition, such as GOOD, OK, or LOW. Distinct from the numeric batteryLevel percentage.

bleDeviceType	string
example: BIKE_TRAINER
Bluetooth Low Energy device type name, such as HEART_RATE or BIKE_TRAINER. Applicable to sensors whose sourceType is BLUETOOTH_LOW_ENERGY.

productName	string
example: HRM-Pro
Name of the sensor or accessory product, when available.

batteryLevel	integer($int32)
example: 85
Remaining sensor battery charge as a percentage, when available.

}
```

### ActivityImageDTO

```text
ActivityImageDTO{
url	string
smallUrl	string
mediumUrl	string
expirationTimestamp	integer($int64)
Image url will not be accessible after the expiration time. Null if image url will not expire

}
```

### EBikeAssistModeInfoDTO

```text
EBikeAssistModeInfoDTO{
description:
Maps an e-bike assist mode identifier to its name, as reported in an assist mode information message recorded during the activity.

ebikeAssistMode	integer($int32)
Numeric e-bike assist mode identifier. Use ebikeAssistModeName for the corresponding name.

ebikeAssistModeName	string
example: Eco
E-bike assist mode name corresponding to ebikeAssistMode. Illustrative names include Eco, Tour, Sport, and Turbo; actual names depend on the e-bike and are not a fixed set.

}
```

### CalendarEventInfoDTO

```text
CalendarEventInfoDTO{
description:
Completion target and personalized goal associated with the activity's linked calendar event. Each value is paired with a unit type indicating distance or time. For multisport events, these values may describe an individual leg or transition.

completionTargetValue	number($float)
Completion target for the linked calendar event, in meters when completionTargetUnitType is distance or seconds when it is time.

completionTargetUnitType	string
Type of completion target: distance indicates completionTargetValue is in meters; time indicates it is in seconds.

Enum:
Array [ 2 ]
customGoalValue	number($float)
User entered goal for the linked calendar event, in meters when customGoalUnitType is distance or seconds when it is time.

customGoalUnitType	string
Type of user entered goal: distance indicates customGoalValue is in meters; time indicates it is in seconds.

Enum:
Array [ 2 ]
}
```

### SummaryDTO

```text
SummaryDTO{
startTimeLocal	string
pattern: ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+$
example: 2022-08-10T09:47:59.031
ISO 8601 timestamp in the local time of the activity's time zone, represented without a GMT offset or trailing 'Z'

startTimeGMT	string
pattern: ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+$
example: 2022-08-10T09:47:59.031
ISO 8601 timestamp in UTC, represented without a GMT offset or trailing 'Z'

startLatitude	number($double)
The start latitude for the activity, in decimal degrees

startLongitude	number($double)
The start longitude for the activity, in decimal degrees

distance	number($double)
The distance for the activity, in meters

duration	number($double)
The duration for the activity, in seconds

movingDuration	number($double)
The moving duration for the activity, in seconds

elapsedDuration	number($double)
The elapsed duration for the activity, in seconds

elevationGain	number($double)
The elevation gain for the activity, in meters

elevationLoss	number($double)
The elevation loss for the activity, in meters

maxElevation	number($double)
The maximum elevation for the activity, in meters

minElevation	number($double)
The minimum elevation for the activity, in meters

avgElevation	number($double)
Average elevation of the activity in meters

averageSpeed	number($double)
The average speed for the activity, in meters per second

averageMovingSpeed	number($double)
The average moving speed for the activity, in meters per second

maxSpeed	number($double)
The maximum speed for the activity, in meters per second

calories	number($double)
The calories for the activity, in kilocalories

bmrCalories	number($double)
The BMR calories for the activity, in kilocalories

averageHR	number($double)
The average heart rate for the activity, in beats per minute

maxHR	number($double)
The maximum heart rate for the activity, in beats per minute

minHR	number($double)
The minimum heart rate for the activity, in beats per minute

averageRunCadence	number($double)
The average run cadence for the activity, in steps per minute

maxRunCadence	number($double)
The maximum run cadence for the activity, in steps per minute

maxLapAvgRunCadence	number($double)
The maximum lap average run cadence for the activity, in steps per minute

averageBikeCadence	number($double)
The average bike cadence for the activity, in revolutions per minute

maxBikeCadence	number($double)
The maximum bike cadence for the activity, in revolutions per minute

averageSwimCadence	number($double)
The average swim cadence for the activity, in strokes per minute

maxSwimCadence	number($double)
The maximum swim cadence for the activity, in strokes per minute

averageTemperature	number($double)
The average temperature for the activity, in degrees Celsius

maxTemperature	number($double)
The maximum temperature for the activity, in degrees Celsius

minTemperature	number($double)
The minimum temperature for the activity, in degrees Celsius

averagePower	number($double)
The average power for the activity, in watts

maxPower	number($double)
The maximum power for the activity, in watts

maxPowerTwentyMinutes	number($double)
The maximum power twenty minutes for the activity, in watts

minPower	number($double)
The minimum power for the activity, in watts

normalizedPower	number($double)
The normalized power for the activity, in watts

functionalThresholdPower	number($double)
The functional threshold power for the activity, in watts

totalWork	number($double)
The total work for the activity, in kilocalories

leftBalance	number($double)
The left balance for the activity

rightBalance	number($double)
The right balance for the activity

leftTorqueEffectiveness	number($double)
The left torque effectiveness for the activity

rightTorqueEffectiveness	number($double)
The right torque effectiveness for the activity

leftPedalSmoothness	number($double)
The left pedal smoothness for the activity

rightPedalSmoothness	number($double)
The right pedal smoothness for the activity

groundContactTime	number($double)
The ground contact time for the activity, in milliseconds

groundContactBalanceLeft	number($double)
The ground contact balance left for the activity

strideLength	number($double)
Stride length for the activity, in centimeters

verticalOscillation	number($double)
The vertical oscillation for the activity, in centimeters

trainingEffect	number($double)
The training effect for the activity

anaerobicTrainingEffect	number($double)
The anaerobic training effect for the activity

aerobicTrainingEffectMessage	string
Aerobic training-effect classification for the activity

Enum:
Array [ 25 ]
anaerobicTrainingEffectMessage	string
Anaerobic training-effect classification for the activity

Enum:
Array [ 17 ]
trainingStressScore	number($double)
The training stress score for the activity

intensityFactor	number($double)
The intensity factor for the activity, in percent

poolLength	number($double)
Pool length; its unit is provided by unitOfPoolLength.

numberOfActiveLengths	integer($int32)
Number of active lengths recorded for the activity

unitOfPoolLength	{...}
totalNumberOfStrokes	integer($int32)
Total number of strokes recorded for the activity

averageStrokes	number($double)
Average number of strokes per active length for the activity

minimumStrokes	number($double)
Minimum number of strokes recorded for a length in the activity

averageSWOLF	number($double)
The average SWOLF for the activity

minSWOLF	number($double)
The minimum SWOLF for the activity

strokeDistance	number($double)
The stroke distance for the activity, in meters

standingCount	integer($int32)
Number of standing periods recorded for the activity

seatedTime	number($double)
The seated time for the activity, in seconds

standingTime	number($double)
The standing time for the activity, in seconds

maxSeatedPower	number($double)
The maximum seated power for the activity, in watts

maxStandingPower	number($double)
The maximum standing power for the activity, in watts

averageSeatedPower	number($double)
The average seated power for the activity, in watts

averageStandingPower	number($double)
The average standing power for the activity, in watts

maxSeatedCadence	number($double)
The maximum seated cadence for the activity, in revolutions per minute

maxStandingCadence	number($double)
The maximum standing cadence for the activity, in revolutions per minute

averageSeatedCadence	number($double)
The average seated cadence for the activity, in revolutions per minute

averageStandingCadence	number($double)
The average standing cadence for the activity, in revolutions per minute

leftPowerPhaseStart	number($double)
The left power phase start for the activity

leftPowerPhaseEnd	number($double)
The left power phase end for the activity

leftPowerPhaseArcLength	number($double)
The left power phase arc length for the activity

leftPowerPhaseArcCenter	number($double)
The left power phase arc center for the activity

leftPowerPhasePeakStart	number($double)
The left power phase peak start for the activity

leftPowerPhasePeakEnd	number($double)
The left power phase peak end for the activity

leftPowerPhasePeakArcLength	number($double)
The left power phase peak arc length for the activity

leftPowerPhasePeakArcCenter	number($double)
The left power phase peak arc center for the activity

leftPlatformCenterOffset	number($double)
The left platform center offset for the activity, in millimeters

rightPowerPhaseStart	number($double)
The right power phase start for the activity

rightPowerPhaseEnd	number($double)
The right power phase end for the activity

rightPowerPhaseArcLength	number($double)
The right power phase arc length for the activity

rightPowerPhaseArcCenter	number($double)
The right power phase arc center for the activity

rightPowerPhasePeakStart	number($double)
The right power phase peak start for the activity

rightPowerPhasePeakEnd	number($double)
The right power phase peak end for the activity

rightPowerPhasePeakArcLength	number($double)
The right power phase peak arc length for the activity

rightPowerPhasePeakArcCenter	number($double)
The right power phase peak arc center for the activity

rightPlatformCenterOffset	number($double)
The right platform center offset for the activity, in millimeters

lactateThresholdHeartRate	number($double)
The lactate threshold heart rate for the activity, in beats per minute

averageGforce	number($double)
The average G-force for the activity, in g

maxGforce	number($double)
The maximum G-force for the activity, in g

verticalRatio	number($double)
The vertical ratio for the activity

lactateThresholdSpeed	number($double)
The lactate threshold speed for the activity, in meters per second

directFunctionalThresholdPower	number($double)
The direct functional threshold power for the activity, in watts

distancePerStroke	number($double)
Distance traveled per stroke for the activity, in meters

strokeCadence	number($double)
The stroke cadence for the activity, in strokes per minute

averageStrokeDistance	number($double)
The average stroke distance for the activity, in meters

averageStrokeCadence	number($double)
The average stroke cadence for the activity, in strokes per minute

maxStrokeCadence	number($double)
The maximum stroke cadence for the activity, in strokes per minute

riderPosition	integer($int32)
The rider position for the activity

startTimeGMTDoubleValue	number($double)
Numeric representation of the activity start time in GMT

totalExerciseReps	integer($int32)
Total number of exercise repetitions recorded for the activity

totalReps	integer($int32)
Total number of repetitions recorded for the activity

totalSets	integer($int32)
Total number of exercise sets recorded for the activity

activeSets	integer($int32)
Number of active exercise sets recorded for the activity

maxLapRepCount	integer($int32)
Maximum repetition count recorded for a lap in the activity

maxDepth	number($double)
The maximum depth for the activity, in meters

averageDepth	number($double)
The average depth for the activity, in meters

surfaceInterval	number($double)
The surface interval for the activity, in seconds

startCns	number($double)
The start CNS for the activity

endCns	number($double)
The end CNS for the activity

startN2	number($double)
The start N2 for the activity

endN2	number($double)
The end N2 for the activity

bottomTime	number($double)
The bottom time for the activity, in seconds

maxBottomTime	number($double)
The maximum bottom time for the activity, in seconds

diveAlert	string
The dive alert associated with the activity

endLatitude	number($double)
The end latitude for the activity, in decimal degrees

endLongitude	number($double)
The end longitude for the activity, in decimal degrees

isDecoDive	boolean
Indicates whether the dive was a decompression dive.

floorsClimbed	number($double)
Number of floors climbed during the activity

floorsDescended	number($double)
Number of floors descended during the activity

avgVerticalSpeed	number($double)
The average vertical speed for the activity, in meters per second

maxVerticalSpeed	number($double)
The maximum vertical speed for the activity, in meters per second

perceivedWorkoutEffort	integer($int32)
The perceived workout effort for the activity

flow	number($double)
The flow for the activity

grit	number($double)
The grit for the activity

jumpCount	integer($int32)
Number of jumps recorded for the activity

caloriesEstimated	number($double)
The calories estimated for the activity, in kilocalories

caloriesConsumed	number($double)
The calories consumed for the activity, in kilocalories

waterEstimated	number($double)
The water estimated for the activity, in milliliters

waterConsumed	number($double)
The water consumed for the activity, in milliliters

minRespirationRate	number($double)
The minimum respiration rate for the activity, in breaths per minute

maxRespirationRate	number($double)
The maximum respiration rate for the activity, in breaths per minute

avgRespirationRate	number($double)
The average respiration rate for the activity, in breaths per minute

trainingEffectLabel	string
Training-effect label for the activity

activityTrainingLoad	number($double)
The activity training load for the activity

avgFlow	number($double)
The average flow for the activity

avgGrit	number($double)
The average grit for the activity

minActivityLapDuration	number($double)
The minimum activity lap duration for the activity, in seconds

startStress	number($double)
The start stress for the activity

endStress	number($double)
The end stress for the activity

differenceStress	number($double)
The difference stress for the activity

directWorkoutFeel	integer($int32)
The direct workout feel for the activity

directWorkoutRpe	integer($int32)
The direct workout RPE for the activity

directWorkoutComplianceScore	integer($int32)
The direct workout compliance score for the activity

targetDuration	number($double)
The target duration for the activity, in seconds

targetDistance	number($double)
The target distance for the activity, in meters

targetAverageSpeed	number($double)
The target average speed for the activity, in meters per second

moderateIntensityMinutes	integer($int32)
Total moderate intensity activity time, in minutes.

vigorousIntensityMinutes	integer($int32)
Total vigorous intensity activity time, in minutes.

steps	integer($int32)
Total number of steps recorded for the activity

avgStress	number($double)
maximum: 100
minimum: 0
The average stress for the activity

maxStress	number($double)
maximum: 100
minimum: 0
The maximum stress for the activity

recoveryHeartRate	integer($int32)
The recovery heart rate for the activity, in beats per minute

beginPotentialStamina	number($double)
The begin potential stamina for the activity

endPotentialStamina	number($double)
The end potential stamina for the activity

minAvailableStamina	number($double)
The minimum available stamina for the activity

gainSolarActivityTime	number($double)
The gain solar activity time for the activity, in seconds

avgSolarChargePercent	number($double)
The average solar charge percent for the activity

avgEbikeAssistLevelPercent	number($double)
The average ebike assist level percent for the activity

avgGradeAdjustedSpeed	number($double)
The average grade adjusted speed for the activity, in meters per second

avgWheelchairCadence	number($double)
The average wheelchair cadence for the activity, in strokes per minute

maxWheelchairCadence	number($double)
The maximum wheelchair cadence for the activity, in strokes per minute

avgJumpRopeCadence	number($double)
The average jump rope cadence for the activity, in repetitions per minute

maxJumpRopeCadence	number($double)
The maximum jump rope cadence for the activity, in repetitions per minute

avgElapsedDurationVerticalSpeed	number($double)
The average elapsed duration vertical speed for the activity, in meters per second

surfaceTypeUnpavedPercentage	number($double)
The surface type unpaved percentage for the activity

differenceBodyBattery	integer($int32)
The body battery difference between the start and end of the activity

beginPackWeight	number($double)
minimum: 0
exclusiveMinimum: false
Pack weight (in grams) carried by the user at the start of the activity

impactLoad	number($double)
Mechanical impact on the body post activity(equivalent distance in meters)

stepSpeedLoss	number($double)
Step Speed Loss metric for a running activity (distance in meters)

stepSpeedLossPercent	number($double)
Step Speed Loss Percentage metric for a running activity (in percentage)

diveCount	integer($int32)
Number of dives recorded in the activity

longestPoolApneaInterval	number($double)
The duration of the longest pool apnea interval, in seconds

avgForce	number($double)
Average force applied in the cycling activity (in Newton)

maxForce	number($double)
Max force applied in the cycling activity (in Newton)

normalizedForce	number($double)
Normalized force applied in the cycling activity (in Newton)

poolApneaBreathHoldDuration	number($double)
The total pool apnea breath hold time duration, in seconds

avgSpo2	integer($int32)
The average saturated pulse Ox value, in percentage

minSpo2	integer($int32)
The minimum saturated pulse Ox value, in percentage

maxSpo2	integer($int32)
The maximum saturated pulse Ox value, in percentage

carbonOffset	number($double)
The carbon offset of the activity expressed in grams of CO2

packWeightCalories	integer($int32)
Calories burned due to pack weight during the activity, in kilocalories

decoDive	boolean
Indicates whether the activity was a decompression dive.

}
```

### UnitDTO

```text
UnitDTO{
unitKey	string
example: kilogram
Case-sensitive identifier for the unit of the associated measurement, such as kilogram or pound for weight, or meter or foot for distance.

}
```

### DiveInfoDTO

```text
DiveInfoDTO{
description:
Dive-specific information combining data recorded by the dive computer with user-entered details about equipment, conditions, and dive buddies.

weight	number($double)
example: 6
Weight used for the dive, expressed in the unit identified by weightUnit.unitKey.

weightUnit	{...}
example: OrderedMap { "unitKey": "kilogram" }
exposureSuit	string
example: Wetsuit
User-entered type or description of the exposure suit worn during the dive.

suitThickness	number($double)
example: 5
Exposure suit thickness, in millimeters.

visibility	number($double)
example: 15
Underwater visibility distance, expressed in the unit identified by visibilityUnit.unitKey.

visibilityUnit	{...}
example: OrderedMap { "unitKey": "meter" }
surfaceCondition	string
example: Calm
User-entered description of water conditions at the surface.

current	string
example: Mild
User-entered description of the water current during the dive.

entryType	string
example: Shore
User-entered method or location of entry into the water.

equipments	string
example: Mask, fins, and buoyancy compensator
User-entered equipment details for the dive, returned as a single string rather than an array.

buddy	string
User-entered name or description of the dive buddy or buddies.

diveSettings	{...}
diveGases	[...]
totalSurfaceTime	integer($int64)
example: 300
Total surface interval time, in seconds, accumulated from the dive summaries associated with the activity.

}
```

### DiveSettingsDTO

```text
DiveSettingsDTO{
description:
Dive computer settings associated with the activity. Model, water type, and setpoint switch modes use numeric codes. Closed-circuit rebreather (CCR) fields describe oxygen partial pressure (PO2) setpoints and their switching behavior.

name	string
example: Default
Name of the dive settings profile.

model	integer($int32)
example: 0
Tissue model code used for decompression calculations; 0 identifies ZHL_16C.

gfLow	integer($int32)
example: 30
Low gradient factor used to control decompression conservatism, expressed as a percentage.

gfHigh	integer($int32)
example: 70
High gradient factor used to control decompression conservatism, expressed as a percentage.

waterType	integer($int32)
example: 1
Water type code: 0 for fresh water, 1 for salt water, 2 for the EN13319 reference or 3 for custom density

waterDensity	number($float)
example: 1025
Water density, in kilograms per cubic meter (kg/m^3). Typical values are 1000 for fresh water and 1025 for salt water; a custom water type permits a custom density.

ccrLowSetpointSwitchMode	integer($int32)
example: 1
Switching mode for the CCR low oxygen partial pressure setpoint: 0 for manual or 1 for automatic.

ccrLowSetpoint	number($float)
example: 0.7
Target oxygen partial pressure (PO2) for the CCR low setpoint, as recorded by the dive computer.

ccrLowSetpointDepth	number($float)
example: 6
Depth, in meters, at which the dive computer switches to the CCR low setpoint when automatic switching is enabled.

ccrHighSetpointSwitchMode	integer($int32)
Switching mode for the CCR high oxygen partial pressure setpoint: 0 for manual or 1 for automatic

ccrHighSetpoint	number($float)
example: 1.3
Target oxygen partial pressure (PO2) for the CCR high setpoint, as recorded by the dive computer.

ccrHighSetpointDepth	number($float)
example: 20
Depth, in meters, at which the dive computer switches to the CCR high setpoint when automatic switching is enabled.

}
```

### DiveGasDTO

```text
DiveGasDTO{
description:
Gas mixture and associated tank information for a dive. Includes gas composition and configuration recorded by the dive computer, plus manually entered volume, tank, pressure, and consumption details when available.

heliumContent	integer($int32)
example: 0
Helium content of the gas mixture, expressed as a percentage.

oxygenContent	integer($int32)
example: 21
Oxygen content of the gas mixture, expressed as a percentage.

status	integer($int32)
example: 1
Dive gas status code: 0 for disabled, 1 for enabled or 2 for backup only.

gasIndex	integer($int32)
example: 0
Zero-based index identifying the gas in the dive gas list. Index 0 represents the bottom gas.

volume	number($double)
example: 12
Manually entered gas volume, expressed in the unit identified by volumeUnit.unitKey. This field is not supplied by the device's dive gas message.

volumeUnit	{...}
example: OrderedMap { "unitKey": "liter" }
tankType	string
example: Steel
User-entered tank material or type, such as steel, aluminum, or other.

tankStartingPressure	number($double)
example: 200
Tank pressure at the start of the dive, expressed in the unit identified by tankStartingPressureUnit.

tankStartingPressureUnit	{...}
example: OrderedMap { "unitKey": "bar" }
tankEndingPressure	number($double)
example: 50
Tank pressure at the end of the dive, expressed in the unit identified by tankEndingPressureUnit.unitKey.

tankEndingPressureUnit	{...}
example: OrderedMap { "unitKey": "bar" }
tankSize	number($double)
example: 12
Tank size, expressed in the unit identified by tankSizeUnit.unitKey.

tankSizeUnit	{...}
example: OrderedMap { "unitKey": "liter" }
sacRate	number($double)
example: 15
Surface air consumption (SAC) rate associated with the gas.

gasMode	integer($int32)
example: 0
Dive gas mode code: 0 for open circuit or 1 for closed-circuit diluent.

}
```

### SplitSummaryDTO

```text
SplitSummaryDTO{
startTimeLocal	string
pattern: ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+$
example: 2022-08-10T09:47:59.031
ISO 8601 timestamp in the local time of the activity's time zone, represented without a GMT offset or trailing 'Z'

startTimeGMT	string
pattern: ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+$
example: 2022-08-10T09:47:59.031
ISO 8601 timestamp in UTC, represented without a GMT offset or trailing 'Z'

startLatitude	number($double)
The start latitude for the split, in decimal degrees

startLongitude	number($double)
The start longitude for the split, in decimal degrees

distance	number($double)
The distance for the split, in meters

duration	number($double)
The duration for the split, in seconds

movingDuration	number($double)
The moving duration for the split, in seconds

elapsedDuration	number($double)
The elapsed duration for the split, in seconds

elevationGain	number($double)
The elevation gain for the split, in meters

elevationLoss	number($double)
The elevation loss for the split, in meters

maxElevation	number($double)
The maximum elevation for the split, in meters

minElevation	number($double)
The minimum elevation for the split, in meters

avgElevation	number($double)
Average elevation of the activity in meters

averageSpeed	number($double)
The average speed for the split, in meters per second

averageMovingSpeed	number($double)
The average moving speed for the split, in meters per second

maxSpeed	number($double)
The maximum speed for the split, in meters per second

calories	number($double)
The calories for the split, in kilocalories

bmrCalories	number($double)
The BMR calories for the split, in kilocalories

averageHR	number($double)
The average heart rate for the split, in beats per minute

maxHR	number($double)
The maximum heart rate for the split, in beats per minute

minHR	number($double)
The minimum heart rate for the split, in beats per minute

averageRunCadence	number($double)
The average run cadence for the split, in steps per minute

maxRunCadence	number($double)
The maximum run cadence for the split, in steps per minute

maxLapAvgRunCadence	number($double)
The maximum lap average run cadence for the split, in steps per minute

averageBikeCadence	number($double)
The average bike cadence for the split, in revolutions per minute

maxBikeCadence	number($double)
The maximum bike cadence for the split, in revolutions per minute

averageSwimCadence	number($double)
The average swim cadence for the split, in strokes per minute

maxSwimCadence	number($double)
The maximum swim cadence for the split, in strokes per minute

averageTemperature	number($double)
The average temperature for the split, in degrees Celsius

maxTemperature	number($double)
The maximum temperature for the split, in degrees Celsius

minTemperature	number($double)
The minimum temperature for the split, in degrees Celsius

averagePower	number($double)
The average power for the split, in watts

maxPower	number($double)
The maximum power for the split, in watts

maxPowerTwentyMinutes	number($double)
The maximum power twenty minutes for the split, in watts

minPower	number($double)
The minimum power for the split, in watts

normalizedPower	number($double)
The normalized power for the split, in watts

functionalThresholdPower	number($double)
The functional threshold power for the split, in watts

totalWork	number($double)
The total work for the split, in kilocalories

leftBalance	number($double)
The left balance for the split

rightBalance	number($double)
The right balance for the split

leftTorqueEffectiveness	number($double)
The left torque effectiveness for the split

rightTorqueEffectiveness	number($double)
The right torque effectiveness for the split

leftPedalSmoothness	number($double)
The left pedal smoothness for the split

rightPedalSmoothness	number($double)
The right pedal smoothness for the split

groundContactTime	number($double)
The ground contact time for the split, in milliseconds

groundContactBalanceLeft	number($double)
The ground contact balance left for the split

strideLength	number($double)
Stride length for the split, in centimeters

verticalOscillation	number($double)
The vertical oscillation for the split, in centimeters

trainingEffect	number($double)
The training effect for the split

anaerobicTrainingEffect	number($double)
The anaerobic training effect for the split

aerobicTrainingEffectMessage	string
Aerobic training-effect classification for the activity

Enum:
Array [ 25 ]
anaerobicTrainingEffectMessage	string
Anaerobic training-effect classification for the activity

Enum:
Array [ 17 ]
trainingStressScore	number($double)
The training stress score for the split

intensityFactor	number($double)
The intensity factor for the split, in percent

poolLength	number($double)
Pool length; its unit is provided by unitOfPoolLength.

numberOfActiveLengths	integer($int32)
Number of active lengths recorded for the split

unitOfPoolLength	{...}
totalNumberOfStrokes	integer($int32)
Total number of strokes recorded for the split

averageStrokes	number($double)
Average number of strokes per active length for the split

minimumStrokes	number($double)
Minimum number of strokes recorded for a length in the split

averageSWOLF	number($double)
The average SWOLF for the split

minSWOLF	number($double)
The minimum SWOLF for the split

strokeDistance	number($double)
The stroke distance for the split, in meters

standingCount	integer($int32)
Number of standing periods recorded for the split

seatedTime	number($double)
The seated time for the split, in seconds

standingTime	number($double)
The standing time for the split, in seconds

maxSeatedPower	number($double)
The maximum seated power for the split, in watts

maxStandingPower	number($double)
The maximum standing power for the split, in watts

averageSeatedPower	number($double)
The average seated power for the split, in watts

averageStandingPower	number($double)
The average standing power for the split, in watts

maxSeatedCadence	number($double)
The maximum seated cadence for the split, in revolutions per minute

maxStandingCadence	number($double)
The maximum standing cadence for the split, in revolutions per minute

averageSeatedCadence	number($double)
The average seated cadence for the split, in revolutions per minute

averageStandingCadence	number($double)
The average standing cadence for the split, in revolutions per minute

leftPowerPhaseStart	number($double)
The left power phase start for the split

leftPowerPhaseEnd	number($double)
The left power phase end for the split

leftPowerPhaseArcLength	number($double)
The left power phase arc length for the split

leftPowerPhaseArcCenter	number($double)
The left power phase arc center for the split

leftPowerPhasePeakStart	number($double)
The left power phase peak start for the split

leftPowerPhasePeakEnd	number($double)
The left power phase peak end for the split

leftPowerPhasePeakArcLength	number($double)
The left power phase peak arc length for the split

leftPowerPhasePeakArcCenter	number($double)
The left power phase peak arc center for the split

leftPlatformCenterOffset	number($double)
The left platform center offset for the split, in millimeters

rightPowerPhaseStart	number($double)
The right power phase start for the split

rightPowerPhaseEnd	number($double)
The right power phase end for the split

rightPowerPhaseArcLength	number($double)
The right power phase arc length for the split

rightPowerPhaseArcCenter	number($double)
The right power phase arc center for the split

rightPowerPhasePeakStart	number($double)
The right power phase peak start for the split

rightPowerPhasePeakEnd	number($double)
The right power phase peak end for the split

rightPowerPhasePeakArcLength	number($double)
The right power phase peak arc length for the split

rightPowerPhasePeakArcCenter	number($double)
The right power phase peak arc center for the split

rightPlatformCenterOffset	number($double)
The right platform center offset for the split, in millimeters

lactateThresholdHeartRate	number($double)
The lactate threshold heart rate for the split, in beats per minute

averageGforce	number($double)
The average G-force for the split, in g

maxGforce	number($double)
The maximum G-force for the split, in g

verticalRatio	number($double)
The vertical ratio for the split

lactateThresholdSpeed	number($double)
The lactate threshold speed for the split, in meters per second

directFunctionalThresholdPower	number($double)
The direct functional threshold power for the split, in watts

distancePerStroke	number($double)
Distance traveled per stroke for the split, in meters

strokeCadence	number($double)
The stroke cadence for the split, in strokes per minute

averageStrokeDistance	number($double)
The average stroke distance for the split, in meters

averageStrokeCadence	number($double)
The average stroke cadence for the split, in strokes per minute

maxStrokeCadence	number($double)
The maximum stroke cadence for the split, in strokes per minute

riderPosition	integer($int32)
The rider position for the split

startTimeGMTDoubleValue	number($double)
Numeric representation of the activity start time in GMT

totalExerciseReps	integer($int32)
Total number of exercise repetitions recorded for the split

totalReps	integer($int32)
Total number of repetitions recorded for the split

totalSets	integer($int32)
Total number of exercise sets recorded for the split

activeSets	integer($int32)
Number of active exercise sets recorded for the split

maxLapRepCount	integer($int32)
Maximum repetition count recorded for a lap in the split

maxDepth	number($double)
The maximum depth for the split, in meters

averageDepth	number($double)
The average depth for the split, in meters

surfaceInterval	number($double)
The surface interval for the split, in seconds

startCns	number($double)
The start CNS for the split

endCns	number($double)
The end CNS for the split

startN2	number($double)
The start N2 for the split

endN2	number($double)
The end N2 for the split

bottomTime	number($double)
The bottom time for the split, in seconds

maxBottomTime	number($double)
The maximum bottom time for the split, in seconds

diveAlert	string
The dive alert associated with the split

endLatitude	number($double)
The end latitude for the split, in decimal degrees

endLongitude	number($double)
The end longitude for the split, in decimal degrees

isDecoDive	boolean
Indicates whether the dive was a decompression dive.

floorsClimbed	number($double)
Number of floors climbed during the split

floorsDescended	number($double)
Number of floors descended during the split

avgVerticalSpeed	number($double)
The average vertical speed for the split, in meters per second

maxVerticalSpeed	number($double)
The maximum vertical speed for the split, in meters per second

perceivedWorkoutEffort	integer($int32)
The perceived workout effort for the split

flow	number($double)
The flow for the split

grit	number($double)
The grit for the split

jumpCount	integer($int32)
Number of jumps recorded for the split

caloriesEstimated	number($double)
The calories estimated for the split, in kilocalories

caloriesConsumed	number($double)
The calories consumed for the split, in kilocalories

waterEstimated	number($double)
The water estimated for the split, in milliliters

waterConsumed	number($double)
The water consumed for the split, in milliliters

minRespirationRate	number($double)
The minimum respiration rate for the split, in breaths per minute

maxRespirationRate	number($double)
The maximum respiration rate for the split, in breaths per minute

avgRespirationRate	number($double)
The average respiration rate for the split, in breaths per minute

trainingEffectLabel	string
Training-effect label for the activity

activityTrainingLoad	number($double)
The activity training load for the split

avgFlow	number($double)
The average flow for the split

avgGrit	number($double)
The average grit for the split

minActivityLapDuration	number($double)
The minimum activity lap duration for the split, in seconds

startStress	number($double)
The start stress for the split

endStress	number($double)
The end stress for the split

differenceStress	number($double)
The difference stress for the split

directWorkoutFeel	integer($int32)
The direct workout feel for the split

directWorkoutRpe	integer($int32)
The direct workout RPE for the split

directWorkoutComplianceScore	integer($int32)
The direct workout compliance score for the split

targetDuration	number($double)
The target duration for the split, in seconds

targetDistance	number($double)
The target distance for the split, in meters

targetAverageSpeed	number($double)
The target average speed for the split, in meters per second

moderateIntensityMinutes	integer($int32)
Total moderate-intensity activity time for the split, in minutes.

vigorousIntensityMinutes	integer($int32)
Total vigorous-intensity activity time for the split, in minutes.

steps	integer($int32)
Total number of steps recorded for the split

avgStress	number($double)
maximum: 100
minimum: 0
The average stress for the split

maxStress	number($double)
maximum: 100
minimum: 0
The maximum stress for the split

recoveryHeartRate	integer($int32)
The recovery heart rate for the split, in beats per minute

beginPotentialStamina	number($double)
The begin potential stamina for the split

endPotentialStamina	number($double)
The end potential stamina for the split

minAvailableStamina	number($double)
The minimum available stamina for the split

gainSolarActivityTime	number($double)
The gain solar activity time for the split, in seconds

avgSolarChargePercent	number($double)
The average solar charge percent for the split

avgEbikeAssistLevelPercent	number($double)
The average ebike assist level percent for the split

avgGradeAdjustedSpeed	number($double)
The average grade adjusted speed for the split, in meters per second

avgWheelchairCadence	number($double)
The average wheelchair cadence for the split, in strokes per minute

maxWheelchairCadence	number($double)
The maximum wheelchair cadence for the split, in strokes per minute

avgJumpRopeCadence	number($double)
The average jump rope cadence for the split, in repetitions per minute

maxJumpRopeCadence	number($double)
The maximum jump rope cadence for the split, in repetitions per minute

avgElapsedDurationVerticalSpeed	number($double)
The average elapsed duration vertical speed for the split, in meters per second

surfaceTypeUnpavedPercentage	number($double)
The surface type unpaved percentage for the split

differenceBodyBattery	integer($int32)
The body battery difference between the start and end of the activity

beginPackWeight	number($double)
minimum: 0
exclusiveMinimum: false
Pack weight (in grams) carried by the user at the start of the activity

impactLoad	number($double)
Mechanical impact on the body post activity(equivalent distance in meters)

stepSpeedLoss	number($double)
Step Speed Loss metric for a running activity (distance in meters)

stepSpeedLossPercent	number($double)
Step Speed Loss Percentage metric for a running activity (in percentage)

diveCount	integer($int32)
Number of dives recorded in the split

longestPoolApneaInterval	number($double)
The duration of the longest pool apnea interval, in seconds

avgForce	number($double)
Average force applied in the cycling activity (in Newton)

maxForce	number($double)
Max force applied in the cycling activity (in Newton)

normalizedForce	number($double)
Normalized force applied in the cycling activity (in Newton)

poolApneaBreathHoldDuration	number($double)
The total pool apnea breath hold time duration, in seconds

avgSpo2	integer($int32)
The average saturated pulse Ox value, in percentage

minSpo2	integer($int32)
The minimum saturated pulse Ox value, in percentage

maxSpo2	integer($int32)
The maximum saturated pulse Ox value, in percentage

carbonOffset	number($double)
The carbon offset of the activity expressed in grams of CO2

packWeightCalories	integer($int32)
Calories burned due to pack weight during the split, in kilocalories

messageIndex	integer($int32)
Message index for the split

splitType	string
Identifies the activity feature represented by the split's data, such as an interval, climb, or dive.

Enum:
Array [ 59 ]
noOfSplits	integer($int32)
Number of splits represented by this summary

averagePowerTarget	number($double)
The average power target for the split, in watts

numFalls	integer($int32)
Number of falls recorded in the split

numClimbSends	integer($int32)
Number of climbing routes completed in the split

numClimbsAttempted	integer($int32)
Number of climbing attempts in the split

numClimbsCompleted	integer($int32)
Number of climbs completed in the split

maxElevationGain	number($double)
The maximum elevation gain for the split, in meters

averageElevationGain	number($double)
The average elevation gain for the split, in meters

maxDistance	integer($int32)
The maximum distance for the split, in meters

maxDistanceWithPrecision	number($double)
Same as maxDistance, but without precision loss, in meters

maxGradeValue	{...}
mode	string
Activity mode associated with the split

Enum:
Array [ 2 ]
gamesWon	integer($int32)
The number of games won for the session

swimStraightnessScore	integer($int32)
Swim straightness score for the split

swimStraightnessExtraDistance	number($double)
Additional distance caused by deviations from a straight swim path, in meters

weightedMeanBestFiveMaxSpeedOverTenSeconds	number($double)
The weighted mean best five maximum speed over ten seconds for the split, in meters per second

maxPisteDifficulty	string
Maximum piste difficulty rating recorded in the split

Enum:
Array [ 5 ]
avgReactionTime	number($double)
Average reaction time for the split, in seconds

minReactionTime	number($double)
The minimum reaction time for starting a rep, in seconds

avgStepFrequency	number($double)
Average step frequency during the split, in steps per minute

maxStepFrequency	number($double)
The maximum frequency of steps during the activity, in steps per minute

gctAirTimeRatio	number($double)
The ratio of ground contact time to air time, as a percent

maxAcceleration	number($double)
The maximum acceleration during the activity, in meters per second squared

avgMaxAcceleration	number($double)
The average of the maximum accelerations during the activity, in meters per second squared

avgMaxSpeed	number($double)
The average of the maximum speeds during the activity, in meters per second

minStanceTime	number($double)
Minimum stance (ground-contact) time for the split, in milliseconds

avgStanceTime	number($double)
Average stance (ground-contact) time for the split, in milliseconds

avgStanceTimePercent	number($double)
The average stance time (ground contact time) percent

avgStepLength	number($double)
Average step length for the split, in meters

maxStepLength	number($double)
Maximum step length for the split, in meters

avgDistanceToMaxSpeed	number($double)
The average distance to reach the max speed of a split, in meters

avgPackWeight	integer($int32)
The average pack weight for the split, in grams

maxPackWeight	integer($int32)
The maximum pack weight for the split, in grams

maxDuration	number($double)
The maximum duration in seconds

decoDive	boolean
Indicates whether the activity was a decompression dive.

}
```

### GradeValueDTO

```text
GradeValueDTO{
valueKey	string
example: _5_1
Key identifying the climbing grade within the specified scale. For example, _5_1 represents grade 5.1 on the YDS scale.

scale	string
Enum:
Array [ 12 ]
}
```

### VideoGameInfoDTO

```text
VideoGameInfoDTO{
description:
The video game info for eSport activities

name	string
The freeform name of the game

type	string
The type of game played

Enum:
Array [ 5 ]
}
```

### DeviceDisplayUnitsDTO

```text
DeviceDisplayUnitsDTO{
description:
The device display units. Currently only populated on Fly activities

distanceDisplayMeasure	string
Distance display measure from the device

elevationDisplayMeasure	string
Elevation display measure from the device

speedDisplayMeasure	string
Speed display measure from the device

verticalSpeedDisplayMeasure	string
Vertical speed display measure from the device

}
```

### ActivityWorkoutDTO

```text
ActivityWorkoutDTO{
index	integer($int32)
workoutName	string
Name of the workout performed during the activity.

timeCreated	string
pattern: ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+$
example: 2022-08-10T09:47:59.031
ISO 8601 timestamp in UTC, represented without a GMT offset or trailing 'Z'

sport	string
example: RUNNING
Sport the workout is intended for, such as RUNNING, CYCLING, or SWIMMING.

manufacturer	string
example: GARMIN
Manufacturer associated with the workout, such as GARMIN.

multisportSet	integer($int32)
If the value is in the closed range 0-99, then a multisport transition reset should be performed in between the legs (record a multisport activity). If the value is in the closed range 100-254, then the legs (sessions) should be performed as separate workouts (2 separate activities but still back-to-back). If the value is 255 - the workouts were not intended to be grouped (2 separate activities recorded some time on the same day, but not necessarily back to back)

steps	[...]
workoutPhrase	string
example: ANAEROBIC_SPEED
readOnly: true
Identifier for the adaptive coaching message associated with the workout, describing its training focus or recommendation context.

}
```

### WorkoutStepDTO

```text
WorkoutStepDTO{
description:
An individual step or repeat instruction in the activity's structured workout. Describes when the step ends, its training target, and optional exercise details. Numeric duration and target values must be interpreted together with their type identifiers.

stepIndex	integer($int32)
example: 0
Zero-based index identifying the step within the workout. Repeat instructions use these indices to identify the step to return to.

name	string
example: Warm up
Name of the workout step, when supplied. May be null or blank.

intensity	string
example: WARMUP
Role or effort classification of the step, such as ACTIVE, WARMUP, COOLDOWN, REST, or RECOVERY.

durationType	string
example: TIME
Condition that ends the step, such as TIME, DISTANCE, REPS, HR_LESS_THAN, HR_GREATER_THAN, OPEN for no fixed duration, and REPEAT_UNTIL_STEPS_CMPLT for a repeat group.

durationValue	number($double)
example: 300
Value for the step's end condition: seconds for TIME, meters for DISTANCE, or repetition count for REPS. For repeat instructions, this is the stepIndex to return to, not elapsed time. Heart-rate thresholds use percentage of maximum heart rate or bpm + 100; power thresholds use percentage of functional threshold power (FTP) or watts + 1000.

targetType	string
example: HEART_RATE
Training target for the step, returned as an uppercase identifier such as HEART_RATE, SPEED, CADENCE, POWER, or SWIM_STROKE. OPEN indicates no specific target. Repeat instructions are interpreted using durationType instead.

targetValue	number($double)
example: 0
Target selector whose meaning depends on the step type. For speed, heart-rate, cadence, or power zones, 0 selects a custom range defined by targetValueLow and targetValueHigh; a nonzero value selects a zone. For REPEAT_UNTIL_STEPS_CMPLT, this is the repeat count; other repeat types use it as their stopping threshold, such as seconds for REPEAT_UNTIL_TIME or meters for REPEAT_UNTIL_DISTANCE.

targetValueLow	number($double)
example: 250
Lower bound of a custom target range. Speed is in meters per second. Heart rate uses percentage of maximum heart rate or bpm + 100 (250 means 150 bpm). Power uses percentage of FTP or watts + 1000. Cadence is in revolutions per minute, or steps per minute for running workouts.

targetValueHigh	number($double)
example: 270
Upper bound of a custom target range, using the same units and encoding as targetValueLow. For a heart-rate target, 270 represents 170 bpm.

notes	string
example: Maintain a steady effort.
Free-text instructions or notes associated with the step.

equipmentType	string
example: SWIM_KICKBOARD
Equipment associated with the step, returned as an uppercase identifier such as NONE, SWIM_FINS, SWIM_KICKBOARD, or SWIM_PULL_BUOY.

exerciseCategory	string
example: BENCH_PRESS
Exercise category associated with the step, returned as an uppercase identifier such as BENCH_PRESS. Used with exerciseName to identify a specific exercise.

exerciseName	string
example: BARBELL_BENCH_PRESS
Specific exercise within exerciseCategory, returned as an uppercase identifier rather than localized display text.

exerciseWeightValue	number($double)
example: 20
Exercise weight, in kilograms, when available. The numeric value remains in kilograms regardless of weightDisplayUnit.

weightDisplayUnit	string
example: KILOGRAM
Preferred unit for displaying exerciseWeightValue, returned as an uppercase identifier such as KILOGRAM or POUND. Does not change the unit of the returned numeric weight.

}
example: OrderedMap { "stepIndex": 0, "name": "Warm up", "intensity": "WARMUP", "durationType": "TIME", "durationValue": 300, "targetType": "HEART_RATE", "targetValue": 0, "targetValueLow": 250, "targetValueHigh": 270, "notes": "Maintain a steady effort" }
```

### SummarizedActivityDTO

```text
SummarizedActivityDTO{
activityId	integer($int64)
Unique identifier of the activity

activityName	string
Name of the activity

description	string
User provided description of the activity

startTimeLocal	string
pattern: ^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$
example: 2026-08-31 17:01:18
Activity start date and time in the local time zone, in yyyy-MM-dd HH:mm:ss format without a UTC offset

startTimeGMT	string
pattern: ^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$
example: 2026-08-31 22:01:18
Activity start date and time in GMT (UTC), in yyyy-MM-dd HH:mm:ss format without a UTC offset suffix

activityType	{...}
example: OrderedMap { "typeId": 1, "typeKey": "running", "parentTypeId": 17 }
eventType	{...}
comments	[...]
isFavorite	boolean
Indicates whether the user marked the activity as a favorite.

isPR	boolean
Indicates whether the activity is a personal record.

isAutoCalcCalories	boolean
Indicates whether calories were automatically calculated for the activity.

isParent	boolean
Indicates whether the activity is a parent activity.

parentId	integer($int64)
Identifier of the parent activity

distance	number($double)
The distance for the activity, in meters

duration	number($double)
example: 2400.931884765625
The duration for the activity, in seconds

elapsedDuration	number($double)
example: 2404.966064453125
The elapsed duration for the activity, in seconds

movingDuration	number($double)
example: 2396.947021484375
The moving duration for the activity, in seconds

elevationGain	number($double)
The elevation gain for the activity, in meters

elevationLoss	number($double)
The elevation loss for the activity, in meters

averageSpeed	number($double)
The average speed for the activity, in meters per second

maxSpeed	number($double)
The maximum speed for the activity, in meters per second

startLatitude	number($double)
The start latitude for the activity, in decimal degrees

startLongitude	number($double)
The start longitude for the activity, in decimal degrees

hasPolyline	boolean
Indicates whether the activity has a polyline.

hasImages	boolean
Indicates whether the activity has images.

ownerId	integer($int64)
Identifier of the activity owner

ownerDisplayName	string
The owner display name associated with the activity

ownerFullName	string
The owner full name associated with the activity

ownerProfileImageUrlSmall	string
The owner profile image url small associated with the activity

ownerProfileImageUrlMedium	string
The owner profile image url medium associated with the activity

ownerProfileImageUrlLarge	string
The owner profile image url large associated with the activity

calories	number($double)
The calories for the activity, in kilocalories

bmrCalories	number($double)
The BMR calories for the activity, in kilocalories

averageHR	number($double)
The average heart rate for the activity, in beats per minute

maxHR	number($double)
The maximum heart rate for the activity, in beats per minute

averageRunningCadenceInStepsPerMinute	number($double)
The average running cadence for the activity, in steps per minute

maxRunningCadenceInStepsPerMinute	number($double)
The maximum running cadence for the activity, in steps per minute

maxLapAvgRunCadence	number($double)
The maximum lap average run cadence for the activity, in steps per minute

averageBikingCadenceInRevPerMinute	number($double)
The average biking cadence in rev per minute for the activity, in revolutions per minute

maxBikingCadenceInRevPerMinute	number($double)
The maximum biking cadence in rev per minute for the activity, in revolutions per minute

averageSwimCadenceInStrokesPerMinute	number($double)
The average swim cadence in strokes per minute for the activity, in strokes per minute

maxSwimCadenceInStrokesPerMinute	number($double)
The maximum swim cadence in strokes per minute for the activity, in strokes per minute

averageSwolf	number($double)
The average SWOLF for the activity

activeLengths	integer($int64)
Number of active lengths recorded for the activity

steps	integer($int64)
Total number of steps recorded for the activity

numberOfActivityLikes	integer($int32)
Number of likes associated with the activity

numberOfActivityComments	integer($int32)
Number of comments associated with the activity

likedByUser	boolean
Indicates whether the current user has liked the activity.

commentedByUser	boolean
Indicates whether the current user has commented on the activity.

activityLikeDisplayNames	[...]
activityLikeFullNames	[...]
activityLikeProfileImageUrls	[...]
requestorRelationship	string
The requestor relationship associated with the activity

privacy	{...}
poolLength	number($double)
Pool length, in centimeters. The current implementation returns the normalized value without conversion, even when unitOfPoolLength indicates meters or yards.

unitOfPoolLength	{...}
hasVideo	boolean
Indicates whether the activity has a video.

videoUrl	string
The video url associated with the activity

beginTimestamp	integer($int64)
example: 1788213678000
Activity start timestamp, in milliseconds since the Unix epoch (1970-01-01T00:00:00Z)

sportTypeId	integer($int32)
Identifier of the sport type

avgPower	number($double)
The average power for the activity, in watts

maxPower	number($double)
The maximum power for the activity, in watts

aerobicTrainingEffect	number($double)
The aerobic training effect for the activity

anaerobicTrainingEffect	number($double)
The anaerobic training effect for the activity

strokes	number($double)
Total number of strokes recorded for the activity

normPower	number($double)
The norm power for the activity, in watts

leftBalance	number($double)
The left balance for the activity

rightBalance	number($double)
The right balance for the activity

avgLeftBalance	number($double)
The average left balance for the activity

max20MinPower	number($double)
Maximum average power over a 20-minute interval for the activity, in watts

avgVerticalOscillation	number($double)
The average vertical oscillation for the activity, in centimeters

avgGroundContactTime	number($double)
The average ground contact time for the activity, in milliseconds

avgStrideLength	number($double)
Average stride length for the activity, in centimeters

avgFractionalCadence	number($double)
The average fractional cadence for the activity, in steps per minute

maxFractionalCadence	number($double)
The maximum fractional cadence for the activity, in steps per minute

trainingStressScore	number($double)
The training stress score for the activity

intensityFactor	number($double)
The intensity factor for the activity, expressed as a percentage in decimal form (for example, 0.80 represents 80%)

vO2MaxValue	number($double)
The vo2max value for the activity

avgVerticalRatio	number($double)
The average vertical ratio for the activity

avgGroundContactBalance	number($double)
The average ground contact balance for the activity

lactateThresholdBpm	number($double)
Lactate-threshold heart rate for the activity, in beats per minute

getlactateThresholdSpeed	number($double)
The lactate threshold speed for the activity, in centimeters per millisecond

maxFtp	number($double)
The maximum FTP for the activity, in watts

avgStrokeDistance	number($double)
The average stroke distance for the activity, in centimeters

avgStrokeCadence	number($double)
The average stroke cadence for the activity, in strokes per minute

maxStrokeCadence	number($double)
The maximum stroke cadence for the activity, in strokes per minute

avgStrokes	number($double)
Average number of strokes per active length for the activity

minStrokes	number($double)
Minimum number of strokes recorded for a length in the activity

minTemperature	number($double)
The minimum temperature for the activity, in degrees Celsius

maxTemperature	number($double)
The maximum temperature for the activity, in degrees Celsius

minElevation	number($double)
The minimum elevation for the activity, in meters

maxElevation	number($double)
The maximum elevation for the activity, in meters

avgElevation	number($double)
The average elevation of the activity in meters

avgDoubleCadence	number($double)
The average double cadence for the activity, in steps per minute

maxDoubleCadence	number($double)
The maximum double cadence for the activity, in steps per minute

isElevationCorrected	boolean
Indicates whether elevation data for the activity has been corrected.

summarizedExerciseSets	[...]
maxDepth	number($double)
The maximum depth for the activity, in centimeters

avgDepth	number($double)
The average depth for the activity, in centimeters

surfaceInterval	number($double)
The surface interval for the activity, in milliseconds

startN2	number($double)
The start N2 for the activity

endN2	number($double)
The end N2 for the activity

startCns	number($double)
The start CNS for the activity

endCns	number($double)
The end CNS for the activity

isDecoDive	boolean
Indicates whether the dive was a decompression dive.

summarizedDiveInfo	{...}
diveCount	integer($int32)
Number of dives recorded in the activity

activityLikeAuthors	[...]
avgVerticalSpeed	number($double)
The average vertical speed for the activity, in meters per second

maxVerticalSpeed	number($double)
The maximum vertical speed for the activity, in meters per second

floorsClimbed	number($double)
Number of floors climbed during the activity

floorsDescended	number($double)
Number of floors descended during the activity

manufacturer	string
The manufacturer associated with the activity

diveNumber	integer($int64)
Sequential dive number for the activity

locationName	string
Location name associated with the activity

bottomTime	number($double)
The bottom time for the activity, in seconds

lapCount	integer($int32)
Number of laps recorded for the activity

endLatitude	number($double)
The end latitude for the activity, in decimal degrees

endLongitude	number($double)
The end longitude for the activity, in decimal degrees

flow	number($double)
The flow for the activity

grit	number($double)
The grit for the activity

jumpCount	integer($int32)
Number of jumps recorded for the activity

caloriesEstimated	number($double)
The energy expenditure estimated for the activity, in kilojoules

caloriesConsumed	number($double)
The energy consumed for the activity, in kilojoules

waterEstimated	number($double)
The water estimated for the activity, in milliliters

waterConsumed	number($double)
The water consumed for the activity, in milliliters

maxAvgPower_1	integer($int32)
Maximum average power over a 1-second interval for the activity, in watts

maxAvgPower_2	integer($int32)
Maximum average power over a 2-second interval for the activity, in watts

maxAvgPower_5	integer($int32)
Maximum average power over a 5-second interval for the activity, in watts

maxAvgPower_10	integer($int32)
Maximum average power over a 10-second interval for the activity, in watts

maxAvgPower_20	integer($int32)
Maximum average power over a 20-second interval for the activity, in watts

maxAvgPower_30	integer($int32)
Maximum average power over a 30-second interval for the activity, in watts

maxAvgPower_60	integer($int32)
Maximum average power over a 60-second interval for the activity, in watts

maxAvgPower_120	integer($int32)
Maximum average power over a 120-second interval for the activity, in watts

maxAvgPower_300	integer($int32)
Maximum average power over a 300-second interval for the activity, in watts

maxAvgPower_600	integer($int32)
Maximum average power over a 600-second interval for the activity, in watts

maxAvgPower_1200	integer($int32)
Maximum average power over a 1200-second interval for the activity, in watts

maxAvgPower_1800	integer($int32)
Maximum average power over a 1800-second interval for the activity, in watts

maxAvgPower_3600	integer($int32)
Maximum average power over a 3600-second interval for the activity, in watts

maxAvgPower_7200	integer($int32)
Maximum average power over a 7200-second interval for the activity, in watts

maxAvgPower_18000	integer($int32)
Maximum average power over a 18000-second interval for the activity, in watts

excludeFromPowerCurveReports	boolean
Indicates whether the activity is excluded from power curve reports.

totalSets	integer($int32)
Total number of exercise sets recorded for the activity

activeSets	integer($int32)
Number of active exercise sets recorded for the activity

totalReps	integer($int32)
Total number of repetitions recorded for the activity

minRespirationRate	number($double)
The minimum respiration rate for the activity, in breaths per minute

maxRespirationRate	number($double)
The maximum respiration rate for the activity, in breaths per minute

avgRespirationRate	number($double)
The average respiration rate for the activity, in breaths per minute

trainingEffectLabel	string
Training-effect label for the activity

activityTrainingLoad	number($double)
The activity training load for the activity

avgFlow	number($double)
The average flow for the activity

avgGrit	number($double)
The average grit for the activity

minActivityLapDuration	number($double)
example: 1199.947021484375
The minimum activity lap duration for the activity, in seconds

avgStress	number($double)
The average stress for the activity

startStress	number($double)
The start stress for the activity

endStress	number($double)
The end stress for the activity

differenceStress	number($double)
The difference stress for the activity

maxStress	number($double)
The maximum stress for the activity

aerobicTrainingEffectMessage	string
Aerobic training-effect classification for the activity

anaerobicTrainingEffectMessage	string
Anaerobic training-effect classification for the activity

splitSummaries	[...]
isManualActivity	boolean
Indicates whether the activity was recorded manually.

moderateIntensityMinutes	integer($int32)
The moderate intensity duration for the activity, in minutes

vigorousIntensityMinutes	integer($int32)
The vigorous intensity duration for the activity, in minutes

maxBottomTime	number($double)
The maximum bottom time for the activity, in seconds

hasSeedFirstbeatProfile	boolean
Indicates whether the activity has a Seed Firstbeat profile.

avgGradeAdjustedSpeed	number($double)
The average grade adjusted speed for the activity, in meters per second

avgWheelchairCadence	number($double)
The average wheelchair cadence for the activity, in strokes per minute

maxWheelchairCadence	number($double)
The maximum wheelchair cadence for the activity, in strokes per minute

avgJumpRopeCadence	number($double)
The average jump rope cadence for the activity, in repetitions per minute

maxJumpRopeCadence	number($double)
The maximum jump rope cadence for the activity, in repetitions per minute

gameName	string
The name of the game being played

differenceBodyBattery	integer($int32)
maximum: 100
minimum: -100
The difference body battery for the activity

gameType	string
The type of game the activity was recorded

Enum:
Array [ 5 ]
beginPackWeight	number($double)
Pack weight carried by the user at the start of the activity, in grams

fastestSplit_1000	number($double)
the time, in seconds, for the fastest 1000 meter split in the activity

fastestSplit_1609	number($double)
the time, in seconds, for the fastest mile split in the activity

fastestSplit_5000	number($double)
the time, in seconds, for the fastest 5k meter split in the activity

fastestSplit_10000	number($double)
the time, in seconds, for the fastest 10k meter split in the activity

fastestSplit_21098	number($double)
the time, in seconds, for the fastest half marathon split in the activity

fastestSplit_42195	number($double)
the time, in seconds, for the fastest marathon split in the activity

fastestSplit_40000	number($double)
the time, in seconds, for the fastest 40k split in the activity

fastestSplit_100	number($double)
the time, in seconds, for the fastest 100 meter split in the activity

fastestSplit_400	number($double)
the time, in seconds, for the fastest 400 meter split in the activity

fastestSplit_750	number($double)
the time, in seconds, for the fastest 750 meter split in the activity

fastestSplit_1500	number($double)
the time, in seconds, for the fastest 1500 meter split in the activity

fastestSplit_91	number($double)
the time, in seconds, for the fastest 100 yard (actually 91.44 meter) split in the activity

fastestSplit_457	number($double)
the time, in seconds, for the fastest 500 yard (actually 457.2 meter) split in the activity

fastestSplit_914	number($double)
the time, in seconds, for the fastest 1000 yard (actually 914.4 meter) split in the activity

fastestSplit_1508	number($double)
the time, in seconds, for the fastest 1650 yard (actually 1508.76 meter) split in the activity

impactLoad	number($double)
Impact on the body post activity(equivalent distance in meters)

avgStepSpeedLoss	number($double)
Step Speed Loss metric for a running activity, expressed as a distance in centimeters

avgStepSpeedLossPercent	number($double)
Step Speed Loss Percentage metric for a running activity, expressed as a percentage

hrTimeInZone_1	number($double)
example: 6.001
The number of seconds that the user's heart rate was in zone 1

hrTimeInZone_2	number($double)
example: 30
The number of seconds that the user's heart rate was in zone 2

hrTimeInZone_3	number($double)
example: 793.001
The number of seconds that the user's heart rate was in zone 3

hrTimeInZone_4	number($double)
example: 1120.344
The number of seconds that the user's heart rate was in zone 4

hrTimeInZone_5	number($double)
example: 446.603
The number of seconds that the user's heart rate was in zone 5

powerTimeInZone_1	number($double)
example: 351.933
The number of seconds that the user's power was in zone 1

powerTimeInZone_2	number($double)
example: 1300.59
The number of seconds that the user's power was in zone 2

powerTimeInZone_3	number($double)
example: 409.005
The number of seconds that the user's power was in zone 3

powerTimeInZone_4	number($double)
example: 224.005
The number of seconds that the user's power was in zone 4

powerTimeInZone_5	number($double)
example: 79.999
The number of seconds that the user's power was in zone 5

powerTimeInZone_6	number($double)
example: 26.005
The number of seconds that the user's power was in zone 6

powerTimeInZone_7	number($double)
example: 8.999
The number of seconds that the user's power was in zone 7

longestPoolApneaInterval	number($double)
The duration of the longest pool apnea interval, in seconds

avgForce	number($double)
Average force applied in the cycling activity (in Newton)

maxForce	number($double)
Max force applied in the cycling activity (in Newton)

normalizedForce	number($double)
Normalized force applied in the cycling activity (in Newton)

poolApneaBreathHoldDuration	number($double)
The total pool apnea breath hold time duration, in seconds

deviceDisplayUnitsDTO	{...}
endTimeGMT	string
pattern: ^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$
example: 2026-08-31 22:41:22
Activity end date and time in GMT (UTC), in yyyy-MM-dd HH:mm:ss format without a UTC offset suffix

qualifyingDive	boolean
Indicates whether the dive meets the qualifying criteria.

multiDayActivityUUIDs	[...]
activityUUID	string($uuid)
UUID of the activity

carbonOffset	number($double)
The carbon offset achieved with this activity expressed in grams

packWeightCalories	integer($int32)
Calories burned due to pack weight during the activity, in kilocalories

standingTime	number($double)
The time spent in the standing position during a cycling activity, in seconds

seatedTime	number($double)
The time spent in the seated position during a cycling activity, in seconds

maxStandingPower	number($double)
The max power while in the standing position during a cycling activity, in watts

maxSeatedPower	number($double)
The max power while in the seated position during a cycling activity, in watts

avgStandingPower	number($double)
The average power while in the standing position during a cycling activity, in watts

avgSeatedPower	number($double)
The average power while in the seated position during a cycling activity, in watts

parent	boolean
Indicates whether the activity is a parent activity.

decoDive	boolean
Indicates whether the activity was a decompression dive.

elevationCorrected	boolean
Indicates whether elevation data for the activity has been corrected.

pr	boolean
Indicates whether the activity is a personal record.

manualActivity	boolean
Indicates whether the activity was recorded manually.

favorite	boolean
Indicates whether the user marked the activity as a favorite.

autoCalcCalories	boolean
Indicates whether calories were automatically calculated for the activity.

}
```

### ActivityCommentDTO

```text
ActivityCommentDTO{
description:
Comment associated with an activity, including its text, author details, creation and update timestamps, likes, and the requesting user's edit and delete permissions

conversationCommentUuid	string
conversationCommentPk	integer($int64)
conversationUuid	string
activityCommentPk	integer($int64)
authorSocProfilePk	integer($int64)
authorDisplayName	string
authorFullName	string
authorUserProfilePk	integer($int64)
authorImageUrl	string
body	string
activityId	integer($int64)
activityCommentLikeCount	integer($int32)
requestorCanEdit	boolean
requestorCanDelete	boolean
authorPro	boolean
createDate	string($date-time)
Comment creation date and time, in RFC 3339 date-time format

lastUpdatedDate	string($date-time)
Comment last update date and time, in RFC 3339 date-time format

activityCommentLikedByUser	boolean
activityCommentLikeDisplayNames	[...]
activityCommentLikeFullNames	[...]
groupPk	integer($int64)
activityCommentLikeAuthors	[...]
}
```

### SummarizedExerciseSet

```text
SummarizedExerciseSet{
category	string
The category associated with the exercise set

subCategory	string
The sub category associated with the exercise set

reps	integer($int32)
The number of reps for the exercise set

volume	integer($int32)
Exercise volume, calculated as weight in grams multiplied by repetitions and summed across the exercise sets

duration	number($double)
The duration for the exercise set, in milliseconds

sets	integer($int32)
The number of sets for the exercise set

maxWeight	integer($int32)
Maximum weight lifted in the exercise set, in grams

peakPower	number($double)
Peak power recorded for the exercise set, in watts

concentricMeanVelocity	number($double)
Mean concentric movement velocity, in centimeters per millisecond

}
```

### SummarizedDiveInfoDTO

```text
SummarizedDiveInfoDTO{
weight	number($double)
Diver weight; its unit is provided by weightUnit.

weightUnit	{...}
visibility	number($double)
Dive visibility; its unit is provided by visibilityUnit.

visibilityUnit	{...}
surfaceCondition	string
The surface condition associated with the dive

current	string
The current associated with the dive

waterType	integer($int32)
Water type code used for the dive settings

waterDensity	number($float)
Water density in kilograms per cubic meter

summarizedDiveGases	[...]
totalSurfaceTime	integer($int64)
Total time spent at the surface, in seconds

}
```

### SummarizedDiveGasDTO

```text
SummarizedDiveGasDTO{
heliumContent	integer($int32)
Helium content of the gas mixture, as a percentage

oxygenContent	integer($int32)
Oxygen content of the gas mixture, as a percentage

gasIndex	integer($int32)
Index of the gas mixture in the dive configuration

gasMode	integer($int32)
Gas mode code for the dive configuration

}
```

### MinimalSplitSummaryDTO

```text
MinimalSplitSummaryDTO{
noOfSplits	integer($int32)
Number of splits represented by this summary

maxGradeValue	{...}
totalAscent	number($double)
The total ascent for the split, in meters

duration	number($double)
The duration for the split, in seconds

splitType	string
Identifies the activity feature represented by the split's data, such as an interval, climb, or dive.

Enum:
Array [ 59 ]
numClimbSends	integer($int32)
Number of climbing routes completed in the split

maxElevationGain	number($double)
The maximum elevation gain for the split, in meters

averageElevationGain	number($double)
The average elevation gain for the split, in meters

maxDistance	integer($int32)
The maximum distance for the split, in meters

maxDistanceWithPrecision	number($double)
Same as maxDistance, but without precision loss, in meters

distance	number($double)
The distance for the split, in meters

averageSpeed	number($double)
The average speed for the split, in meters per second

maxSpeed	number($double)
The maximum speed for the split, in meters per second

mode	string
Activity mode associated with the split

Enum:
Array [ 2 ]
numFalls	integer($int32)
Number of falls recorded in the split

avgStress	number($double)
The average stress across all active rounds

avgStressWin	number($double)
The average stress for winning rounds only

avgStressLoss	number($double)
The average stress for losing rounds only

avgStressDraw	number($double)
The average stress for draw rounds only

gamesWon	integer($int32)
The number of games won

gamesNotWon	integer($int32)
The number of games not won

gamesAverageWon	number($double)
The average games won

elevationLoss	number($double)
The elevation loss for the split, in meters

maxPackWeight	integer($int32)
The maximum pack weight for the split, in grams

avgPackWeight	integer($int32)
The average pack weight for the split, in grams

maxDuration	number($double)
The maximum duration for the split, in seconds

avgReactionTime	number($double)
Average reaction time for the split, in seconds

minReactionTime	number($double)
Minimum reaction time for the split, in seconds

avgDistanceToMaxSpeed	number($double)
Average distance required to reach maximum speed in the split, in meters

avgStepFrequency	number($double)
Average step frequency during the split, in steps per minute

maxStepFrequency	number($double)
Maximum step frequency value for the split

avgStepLength	number($double)
Average step length for the split, in meters

verticalRatio	number($double)
The vertical ratio for the split

verticalOscillation	number($double)
The vertical oscillation for the split, in centimeters

avgGroundContactBalanceLeft	number($double)
The average ground contact balance left for the split

avgGroundContactTime	number($double)
The average ground contact time for the split, in milliseconds

avgStanceTimePercent	number($double)
Average stance-time percentage for the split

}
```

### HeartRateZonesDTO

```text
HeartRateZonesDTO{
description:
Heart rate zone configuration for a sport.

trainingMethod	string
Training method used to calculate the heart rate zones.

Enum:
Array [ 4 ]
restingHeartRateUsed	integer($int32)
Resting heart rate used to calculate the zones.

lactateThresholdHeartRateUsed	integer($int32)
Lactate threshold heart rate used to calculate the zones.

zone1Floor	integer($int32)
Lower boundary of heart rate zone 1.

zone2Floor	integer($int32)
Lower boundary of heart rate zone 2.

zone3Floor	integer($int32)
Lower boundary of heart rate zone 3.

zone4Floor	integer($int32)
Lower boundary of heart rate zone 4.

zone5Floor	integer($int32)
Lower boundary of heart rate zone 5.

maxHeartRateUsed	integer($int32)
Maximum heart rate used to calculate the zones.

restingHrAutoUpdateUsed	boolean
Indicates whether the resting heart rate is automatically updated.

sport	string
Sport for which the heart rate zones are configured.

Enum:
Array [ 5 ]
}
```

### FitnessAgeDTO

```text
FitnessAgeDTO{
chronologicalAge	integer($int32)
The user's actual age.

fitnessAge	number($double)
The user's calculated Fitness Age.

achievableFitnessAge	number($double)
The achievable Fitness Age for the user.

previousFitnessAge	number($double)
Previous Fitness Age for the user.

components	{...}
lastUpdated	string
The timestamp when the Fitness Age information was last updated.

invalidReason	string
If there is no Fitness Age available, the reason why it is missing will be provided.

Enum:
Array [ 4 ]
}
```

### FitnessAgeComponent

```text
FitnessAgeComponent{
value	number
The current value of the component.

targetValue	number
The target value of the component that would result in the best possible Fitness Age.

improvementValue	number
The difference between the current value and the target value.

potentialAge	number
Potential Fitness Age if the user were to achieve the target value for this component.

priority	number
The relative priority of this component.

stale	boolean
Whether the data in this component is considered stale. Stale data means it has not been updated recently and may not reflect the user's current state.

staleInputs	[...]
lastMeasurementDate	string
Last date when the component was measured.

numOfWeeksForIm	integer($int32)
Number of weeks of Intensity Minutes data that was used to calculate Vigorous Days or Vigorous Weeks component.

}
```

### UserGoalsRangeDTO

```text
UserGoalsRangeDTO{
userGoals	[...]
userGoalRanges	[...]
}
```

### UserGoalDTO

```text
UserGoalDTO{
userGoalCategory	string
Category or source of the weight goal.

Enum:
Array [ 6 ]
userGoalType	string
Goal metric. This endpoint returns weight goals measured in grams.

Enum:
Array [ 1 ]
startDate	{...}
endDate	{...}
goalName	string
Display name of the goal.

goalValue	number($double)
Target weight in grams.

updateDate	{...}
createDate	{...}
trackingPeriodType	string
Period over which the goal is tracked.

Enum:
Array [ 7 ]
}
```

### ConnectDate

```text
ConnectDate{
date	string($date-time)
UTC date-time representation.

localDate	string($date)
User-local calendar date.

}
```

### ConnectTimestamp

```text
ConnectTimestamp{
date	string($date-time)
UTC timestamp.

localDate	string($date)
User-local calendar date corresponding to the timestamp.

}
```

### UserGoalHighLowRangeDTO

```text
UserGoalHighLowRangeDTO{
userGoalCategory	string
Category or source of the weight goal range.

Enum:
Array [ 6 ]
userGoalType	string
Goal metric. This endpoint returns weight goal ranges measured in grams.

Enum:
Array [ 1 ]
startDate	{...}
endDate	{...}
lowWeightGoalInGrams	number($double)
Lower weight target in grams.

highWeightGoalInGrams	number($double)
Upper weight target in grams.

weekNum	integer($int32)
Week number when the range belongs to a sequential plan.

trackingPeriodType	string
Period over which the goal range is tracked.

Enum:
Array [ 7 ]
}
```

### HrvChartDTO

```text
HrvChartDTO{
userProfilePk	integer($int64)
hrvSummary	HrvSummaryDTO{...}
hrvReadings	[...]
startTimestampGMT*	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

endTimestampGMT*	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

startTimestampLocal*	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

endTimestampLocal*	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

sleepStartTimestampGMT	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

sleepEndTimestampGMT	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

sleepStartTimestampLocal	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

sleepEndTimestampLocal	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

}
```

### HrvSummaryDTO

```text
HrvSummaryDTO{
description:
Overnight HRV summary data

calendarDate	string
pattern: 2022-08-10
simple date in the YYYY-MM-DD format

weeklyAvg	integer($int32)
average HRV value for the last 7 days

lastNightAvg	integer($int32)
average overnight HRV value

lastNight5MinHigh	integer($int32)
highest overnight average HRV value over a 5-minute period

baseline	BaselineScoreDTO{...}
status	string
HRV status

Enum:
Array [ 6 ]
feedbackPhrase	string
Enum:
Array [ 39 ]
createTimeStamp*	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

}
```

### BaselineScoreDTO

```text
BaselineScoreDTO{
description:
HRV baseline information

lowUpper	integer($int32)
Upper bound of the 'LOW' HRV range

balancedLow	integer($int32)
Lower bound of the 'BALANCED' HRV range

balancedUpper	integer($int32)
Upper bound of the 'BALANCED' HRV range

markerValue	number($float)
Marker value used to mark where the current HRV weekly average falls within the applicable status range

}
```

### HrvReadingDTO

```text
HrvReadingDTO{
hrvValue	integer($int32)
readingTimeGMT*	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

readingTimeLocal*	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

}
```

### HrvDailySummaryDTO

```text
HrvDailySummaryDTO{
hrvSummaries	[...]
userProfilePk	integer($int64)
}
```

### DailyNutritionSummaryDTO

```text
DailyNutritionSummaryDTO{
description:
Summary of goals, nutrients consumed, and discrete events by a user on a given day.

dailyNutritionContent	ThinNutritionContentDTO{...}
dailyNutritionGoals	NutritionGoalsDTO{...}
dayEndTime	LocalTime{...}
example: 18:59
nullable: true
dayStartTime	LocalTime{...}
example: 18:59
nullable: true
loggedFoodsWithServingSizes	[...]
mealDate*	string
example: 2025-04-14
pattern: 2022-08-10
simple date in the YYYY-MM-DD format

mealDetails	[...]
}
```

### ThinNutritionContentDTO

```text
ThinNutritionContentDTO{
description:
All-day summary of calories and other nutrients consumed by the user on the given date.

calories	integer($int32)
example: 2000
minimum: 0
nullable: true
Calories/energy; given in kilocalories (kilocalorie/kcal; i.e.: 4.184 kJ per kcal).

caloriesPercentage	number($double)
minimum: 0
carbs	number($double)
example: 275
minimum: 0
nullable: true
Total carbohydrates; given in grams (g).

protein	number($double)
minimum: 0
nullable: true
Total protein; given in grams (g).

fat	number($double)
minimum: 0
nullable: true
Total fat; given in grams (g).

}
```

### NutritionGoalsDTO

```text
NutritionGoalsDTO{
description:
The portion of the daily nutrition goals that have been allocated.

adjustedCalories	integer($int32)
nullable: true
Adjusted Daily goal for consumed calories/energy, this includes active calories; given in kilogram calories (kilocalorie/kcal; i.e.: 4.184 kJ per kcal).

adjustedCarbs	number($double)
nullable: true
Adjusted Daily goal for consumed carbohydrates, this includes additional carbs added to the base carbs goal, proportional to the additional active calories that were added to adjustedCalories; given in grams (g).

adjustedFat	number($double)
nullable: true
Adjusted Daily goal for consumed fat, this includes additional fat added to the base fat goal, proportional to the additional active calories that were added to adjustedCalories; given in grams (g).

adjustedProtein	number($double)
nullable: true
Adjusted Daily goal for consumed protein, this includes additional protein added to the base protein goal, proportional to the additional active calories that were added to adjustedCalories; given in grams (g).

calories*	integer($int32)
Daily goal for consumed calories/energy; given in kilogram calories (kilocalorie/kcal; i.e.: 4.184 kJ per kcal).

carbs*	number($double)
Daily goal for consumed carbohydrates; given in grams (g).

fat*	number($double)
Daily goal for consumed fat; given in grams (g).

protein*	number($double)
Daily goal for consumed protein; given in grams (g).

}
```

### LocalTime

```text
LocalTime{
description:
The ending time of the period this meal occupies every day. Some meals might not have set time periods, so this value may be null. If set, the value must be in 24h format and should only include hours and minutes and have no date component. If any time unit smaller than minutes is included, it will be truncated.

hour	integer($int32)
minute	integer($int32)
nano	integer($int32)
second	integer($int32)
}
example: 18:59
nullable: true
```

### FoodDTO

```text
FoodDTO{
description:
A serving of food as defined by a nutrition partner/user-created food(custom food).

foodImages	[...]
foodMetaData*	FoodMetadataDTO{...}
isFavorite	boolean
Indicates if the food is marked as favorite by the user.

nutritionContents*	[...]
}
```

### FoodImageDTO

```text
FoodImageDTO{
description:
Represents an image of a food item in a specific size.

imageType	string
example: 0
Type of the image (e.g., 0 for default)

imageUrl	string
example: https://www.foodimagedb.com/food-images/uuid_1024x1024.png
URL of the food image

}
```

### FoodMetadataDTO

```text
FoodMetadataDTO{
description:
Metadata for food items.

brandName	string
example: Nestle
maxLength: 150
minLength: 1
Brand name for this food.

customFoodType	string
example: FOOD
The custom food type identifier. FOOD or RECIPE

Enum:
Array [ 3 ]
foodId	string
example: 5642356
Unique identifier for this food as defined by the system.

foodImageUrl	string
deprecated: true
example: https://www.foodimage.com/test.png
URL to get image of the food from the client.

foodName*	string
example: Toast with Eggs
maxLength: 150
minLength: 1
Nutrition content (calories, carbs, fats, proteins, etc.) for this food for various serving size.

foodType	string
Type of the food Generic or Brand. Only populated for food from FatSecret data source.

Enum:
Array [ 2 ]
imageUuid	string
example: 123e4567-e89b-12d3-a456-426614174000
Image UUID for the food.

languageCode*	string
example: EN
Language Code for this food.

regionCode*	string
example: US
Region Code for this food.

source	string
example: Garmin or FatSecret
Source for this food.

Enum:
Array [ 2 ]
}
```

### NutritionContentDTO

```text
NutritionContentDTO{
description:
Wrapper containing all nutrition contents tracked by a particular food, meal, or date.

addedSugars	number($double)
example: 50
minimum: 0
nullable: true
Total added sugars; given in grams (g).

calcium	number($double)
example: 1.3
minimum: 0
nullable: true
Calcium; given in milligrams (mg).

calories*	integer($int32)
example: 2000
minimum: 0
nullable: true
Calories/energy; given in kilocalories (kilocalorie/kcal; i.e.: 4.184 kJ per kcal).

carbs	number($double)
example: 275
nullable: true
Total carbohydrates; given in grams (g).

cholesterol	number($double)
example: 63
minimum: 0
nullable: true
Cholesterol; given in milligrams (mg).

fat	number($double)
example: 78
nullable: true
Total fat; given in grams (g).

fiber	number($double)
example: 28
minimum: 0
nullable: true
Dietary fiber; given in grams (g).

iron	number($double)
example: 0.018
minimum: 0
nullable: true
Iron; given in milligrams (mg).

monounsaturatedFat	number($double)
example: 22
minimum: 0
nullable: true
Monounsaturated fat; given in grams (g).

numberOfUnits*	number($double)
example: 2
exclusiveMinimum: false
minimum: 0.001
Total units.

polyunsaturatedFat	number($double)
example: 16
minimum: 0
nullable: true
Polyunsaturated fat; given in grams (g).

potassium	number($double)
example: 47
minimum: 0
nullable: true
Potassium; given in milligrams (mg).

protein	number($double)
example: 50
nullable: true
Protein; given in grams (g).

saturatedFat	number($double)
example: 20
minimum: 0
nullable: true
Saturated fat; given in grams (g).

servingId	string
example: 34534
nullable: true
Serving ID representing unique serving for a food.There can be multiple servings for same food.

servingUnit*	string
example: piece or g or cup
maxLength: 100
minLength: 1
Serving unit of the food.

sodium	number($double)
example: 2.3
minimum: 0
nullable: true
Sodium; given in milligrams (mg).

sugar	number($double)
example: 50
minimum: 0
nullable: true
Total sugars; given in grams (g).

transFat	number($double)
example: 2
minimum: 0
nullable: true
Trans fat; given in grams (g).

unitHasServing	boolean
example: true
nullable: true
Indicates if the unit has a serving size defined.

vitaminA	number($double)
example: 62
minimum: 0
nullable: true
Vitamin A; given in micrograms (mcg).

vitaminC	number($double)
example: 0.09
minimum: 0
nullable: true
Vitamin C; given in milligrams (mg).

vitaminD	number($double)
example: 3
minimum: 0
nullable: true
Vitamin D; given in micrograms (mcg).

}
```

### MealDetailsDTO

```text
MealDetailsDTO{
description:
Summary of nutrients consumed by a user during a given meal on some date.

loggedFoods	[...]
meal*	MealDTO{...}
nullable: true
mealNutritionContent*	ThinNutritionContentDTO{...}
mealNutritionGoals	NutritionGoalsDTO{...}
}
```

### LoggedFoodDTO

```text
LoggedFoodDTO{
description:
Logged food details.

customMealId	integer($int64)
example: 12345
Custom Meal Id associated (if any) with the food.

foodImages	[...]
foodInactive	boolean
foodMetaData	FoodMetadataDTO{...}
id	string
example: 12e1d7c0-f79f-458a-91ba-dec2dd35ede1
pattern: ^\d+$
Unique identifier for the custom meal item

isFavorite	boolean
Whether the food is favorited by the user.

logCategory	string
example: REGULAR_LOG
Category of the log event, representing the type of food log action. Possible values: REGULAR_LOG, QUICK_ADD, IMAGE_RECOGNITION, BARCODE etc.

Enum:
Array [ 5 ]
logId	string
example: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Unique identifier (UUID) for the food log this event belongs to.

logSource	string
example: GCM or GCW or DEVICE
Source for this food event.

logTimestamp	string($date-time)
example: 2023-08-01T08:00:00Z
Timestamp for the initiation/firing of this event; always given as an ISO-8601 timestamp and in the UTC timezone. This timestamp does not need to match the mealDate for this event, as users can update food logs for past and future dates.

mealDateTimeWithOffset	string($date-time)
example: 2023-08-01T08:00:00-07:00
Time (with date and timezone offset) user picked when user logged the food.

mealId	integer($int64)
ID of the meal for which this food was logged.

mealTime	string($time)
example: 08:00:00
Time (just to the hour as of now) user picked when user logged the food.

nutritionContent*	NutritionContentDTO{...}
servingQty*	number($double)
example: 1.6
The number of servings being added/removed.

This is NOT the serving size; the given food in each event represents a single serving, regardless of how that serving is defined/measured for that specific food. This field is simply a multiplier to the nutrition content of that serving.

type*	string
example: FOOD
Type of consumable; FOOD or RECIPE

Enum:
Array [ 3 ]
}
```

### MealDTO

```text
MealDTO{
description:
Defines a meal (e.g.: breakfast, lunch, dinner, etc.).

defaultMealName	string
example: BREAKFAST
readOnly: true
This is the default name for each meal. Some meals might have their name changed, this allows you to get it's original name.This will ONLY be populated for the GET meals/{date}, PUT meals/{date}, GET meals/range, and GET metadata endpoint

displayOrder	integer($int32)
example: 2
minimum: 0
nullable: true
readOnly: true
Used to define sort ordering for meal lists; lower numbers will appear earlier, with ties being resolved by sorting alphabetically using the mealName. Meals with no sortIndex will be shown last.

endTime	LocalTime{...}
example: 18:59
nullable: true
goals	NutritionGoalsDTO{...}
mealId	integer($int64)
example: 12345
nullable: true
Meal ID representing unique Id.

mealIndex	integer($int32)
example: 2
maximum: 7
minimum: 1
The index of this meal within the complete list of meals belonging to the current user. The index should remain the same over the lifespan of the meal, and this value should be unique across meals belonging to one user. For default meals, this value will be 1 for BREAKFAST, 2 for LUNCH, 3 for DINNER, and 4 for SNACKS. If a user was given the ability to rename their meals and decided to flip the names of their BREAKFAST and LUNCH meals, the mealIndex value would remain the same.

mealName*	string
example: Lunch
Human-readable name for this meal.

startTime	LocalTime{...}
example: 18:59
nullable: true
translated	boolean
nullable: true
A flag that indicates whether the meal name has been translated.

}
nullable: true
```

### MenstrualCycleSummaryDTO

```text
MenstrualCycleSummaryDTO{
description:
Summary of a user's menstrual cycle information.

analysis	{...}
currentPhase	integer($int32)
Identifier of the current cycle phase (e.g. menstrual, follicular, ovulation, luteal).

cycleType	string
The type of cycle recorded.

dayInCycle	integer($int32)
The day number within the current cycle.

daysUntilNextPhase	integer($int32)
Number of days remaining until the cycle transitions to its next phase.

deliveryDate	{...}
dueDate	{...}
educationContentMod	integer($int32)
Modulus value used to select which rotating educational content to display to the user.

endDate	{...}
feedbackPhrase	string
fertileWindowStart	integer($int32)
isSkinTempMct	boolean
Indicates whether skin temperature data influenced the menstrual cycle tracking (MCT) calculations.

lengthOfCurrentPhase	integer($int32)
The total length, in days, of the current cycle phase.

lengthOfFertileWindow	integer($int32)
The total length, in days, of the fertile window.

lutealPhaseStart	integer($int32)
The day in the cycle on which the luteal phase begins.

numberOfWeek	integer($int32)
The current week number of pregnancy.

overlapCycleList	[...]
periodLength	integer($int32)
predictedCycle	boolean
Indicates whether this cycle is a predicted cycle rather than a logged one.

predictedCycleLength	integer($int32)
The predicted total length, in days, of this cycle.

predictedOvulationDate	{...}
pregnancyCycle	boolean
Indicates whether this cycle represents a pregnancy rather than a regular menstrual cycle.

startDate	{...}
}
```

### MenstrualCycleAnalysisDTO

```text
MenstrualCycleAnalysisDTO{
cycleTypeAnalysis	{...}
perimenopauseDetected	boolean
example: true
Indicates whether perimenopause was detected for the user

}
```

### CycleTypeAnalysisDTO

```text
CycleTypeAnalysisDTO{
description:
Analysis of the user's menstrual cycle type

cycleLengthDeviationDays	integer($int32)
Number of days the cycle length deviates from the user's median cycle length.

cycleStartDate	ConnectDate{...}
cycleType	string
The classified type of the cycle.

cycleVariability	integer($int32)
A measure of how much the user's cycle lengths vary across recent cycles.

cycleVariabilityClassifier	string
A classifier label describing the level of cycle variability.

follicularLengthDeviationDays	integer($int32)
Number of days the follicular phase length deviates from the user's typical length.

hasAmenorrhea	boolean
Indicates whether amenorrhea (absence of menstruation) was detected.

isAtypical	boolean
Indicates whether this cycle was classified as atypical compared to the user's history.

lutealLengthDeviationDays	integer($int32)
Number of days the luteal phase length deviates from the user's typical length.

medianCycleLength	integer($int32)
The user's median cycle length, in days, calculated from recent cycle history.

medianCycleLengthClassifier	string
A classifier label describing the median cycle length.

periodLengthDeviationDays	integer($int32)
Number of days the period length deviates from the user's typical period length.

prolongedPeriods	integer($int32)
Number of recent periods classified as prolonged.

prolongedPeriodsClassifier	string
A classifier label describing whether the user tends to have prolonged periods.

}
```

### OverlapCycle

```text
OverlapCycle{
description:
Represents a cycle that overlaps with another tracked cycle.

periodLength	integer($int32)
The length of the menstrual period for this overlapping cycle.

startDate	ConnectDate{...}
}
```

### DetailedMenstrualCycleDayDTO

```text
DetailedMenstrualCycleDayDTO{
description:
Combined view of a single day's menstrual cycle log, overall cycle summary, and pregnancy weight goals.

dayLog	{...}
daySummary	{...}
weightGoals	{...}
}
```

### DailyMenstrualCycleLogDTO

```text
DailyMenstrualCycleLogDTO{
description:
The user's self-reported menstrual cycle log data for a single calendar day.

babyMovements	[...]
calendarDate	ConnectDate{...}
discharge	[...]
flow	string
The menstrual flow level logged for this day.

hasBabyMovement	boolean
Indicates whether any baby movement was logged for this day.

hasGlucoseLog	boolean
Indicates whether a glucose reading was logged for this day.

moods	[...]
notes	string
Free-text notes entered by the user for this day.

ovulationDay	boolean
Indicates whether this day was marked/predicted as the ovulation day.

reportTimestamp	ConnectTimestamp{...}
sexDrive	string
The sex drive level logged for this day.

sexualActivity	string
The sexual activity type logged for this day.

symptoms	[...]
userProfilePk	integer($int64)
}
```

### BabyMovementDTO

```text
BabyMovementDTO{
count	integer($int32)
The number of movements counted during this entry.

duration	integer($int32)
The duration, in seconds, over which the movements were counted.

movementType	string
The type of movement logged (e.g. kicks, general, hiccups).

startTimestamp	ConnectTimestamp{...}
}
```

### WeightGoalRangeDTO

```text
WeightGoalRangeDTO{
description:
The recommended weight gain range for a given week of pregnancy.

highWeightGoalInGrams	number($double)
The upper bound of the recommended weight gain, in grams.

lowWeightGoalInGrams	number($double)
The lower bound of the recommended weight gain, in grams.

weekNum	integer($int32)
The pregnancy week number this weight goal range applies to.

}
```

### DailySleepDTO

```text
DailySleepDTO{
id	integer($int64)
userProfilePK	integer($int64)
calendarDate	string
Calendar date the sleep is associated with, in yyyy-MM-dd format.

sleepTimeSeconds	integer($int32)
Total measured sleep time in seconds, excluding naps.

napTimeSeconds	integer($int32)
Sum, in seconds, of all naps recorded for this calendar date.

sleepWindowConfirmed	boolean
Whether the sleep window has been confirmed.

sleepWindowConfirmationType	string
Type of the sleep window was confirmed. One of: unconfirmed, device_confirmed, manually_confirmed, auto_confirmed, auto_confirmed_final, off_wrist, enhanced_confirmed, enhanced_confirmed_final.

sleepStartTimestampGMT	string($date-time)
Start of the confirmed/final sleep window, in UTC, in ms.

sleepEndTimestampGMT	string($date-time)
End of the confirmed/final sleep window, in UTC, in ms.

sleepStartTimestampLocal	string($date-time)
Start of the confirmed/final sleep window, in user's local timezone offset, in ms.

sleepEndTimestampLocal	string($date-time)
End of the confirmed/final sleep window, in user's local timezone offset, in ms.

autoSleepStartTimestampGMT	string($date-time)
Start of the auto-detected sleep window.

autoSleepEndTimestampGMT	string($date-time)
End of the auto-detected sleep window.

sleepQualityTypePK	string
Sleep quality classification key (poor, average, good, excellent).

sleepResultTypePK	string
Sleep result classification key: 'bad', 'ok', or 'great'.

unmeasurableSleepSeconds	integer($int32)
Duration in seconds of sleep that could not be classified into deep, light, REM, or awake levels.

deepSleepSeconds	integer($int32)
Duration in seconds spent in deep sleep.

lightSleepSeconds	integer($int32)
Duration in seconds spent in light sleep.

remSleepSeconds	integer($int32)
Duration in seconds spent in REM sleep.

awakeSleepSeconds	integer($int32)
Duration in seconds spent awake during the sleep window.

deviceRemCapable	boolean
Whether the device used to capture this sleep is capable of detecting REM sleep.

sleepFromDevice	boolean
Whether the sleep window/levels were computed by the device's sleep algorithm.

averageSpO2Value	number($double)
lowestSpO2Value	integer($int32)
highestSpO2Value	integer($int32)
numberOfEventsBelowThreshold	integer($int32)
Number of SpO2 readings that fell below the configured alert threshold (spo2Threshold) during sleep.

averageSpO2HRSleep	number($double)
spo2Threshold	integer($int32)
SpO2 percentage alert threshold configured on the device.

averageRespirationValue	number($double)
lowestRespirationValue	number($float)
highestRespirationValue	number($float)
awakeCount	integer($int32)
Number of times the user woke up during the sleep window.

avgSleepStress	number($double)
ageGroup	string
Age group of the user.

Enum:
Array [ 5 ]
avgHeartRate	number($double)
sleepScoreFeedback	string
Feedback categorization of the sleep score.

Enum:
Array [ 38 ]
sleepScoreInsight	string
Insight categorization associated with the sleep score.

Enum:
Array [ 18 ]
sleepScorePersonalizedInsight	string
Personalized insight associated with the sleep score.

Enum:
Array [ 138 ]
sleepScores	{...}
userNote	string
Free-form note entered by the user for this sleep.

kidSleepNote	string
Free-form note entered by a parent/guardian for a child's sleep.

sleepVersion	integer($int32)
sleepNeed	{...}
nextSleepNeed	{...}
dailyNapDTOS	[...]
breathingDisruptionSeverity	string
Severity of breathing disruptions detected during sleep: NONE, LOW, MEDIUM, HIGH, or UNMEASURABLE.

sleepAlignment	{...}
}
```

### SleepScoreItem

```text
SleepScoreItem{
value	integer($int32)
Numeric value, 0-100, of this sleep score component.

qualifierKey	string
Qualitative label for the score (EXCELLENT, GOOD, FAIR, POOR, or INVALID).

optimalStart	number($double)
Lower bound of the optimal range for this score component.

optimalEnd	number($double)
Upper bound of the optimal range for this score component.

idealStartInSeconds	number($double)
Lower bound of the optimal range for this score component, in seconds. Only applicable for the light, deep, and REM components.

idealEndInSeconds	number($double)
Upper bound of the optimal range for this score component, in seconds. Only applicable for the light, deep, and REM components.

}
```

### SleepNeedDTO

```text
SleepNeedDTO{
description:
Sleep need information.

userProfilePk	integer($int64)
calendarDate	string($date)
deviceId	integer($int64)
timestampGmt	string($date-time)
baseline	integer($int32)
Baseline sleep need.

actual	integer($int32)
Actual/recommended sleep need.

feedback	string
trainingFeedback	string
Numeric code describing feedback relating recent training load to the sleep need.

sleepHistoryAdjustment	string
Numeric code describing the adjustment applied to the baseline sleep need based on recent sleep history.

hrvAdjustment	string
Numeric code describing the adjustment applied to the baseline sleep need based on HRV status.

napAdjustment	string
Numeric code describing the adjustment applied to the baseline sleep need based on naps taken.

displayedForTheDay	boolean
Whether this sleep need value has already been displayed to the user for the day.

recommendedBedtimeStartMins	integer($int32)
Start of the recommended bedtime range, in minutes since midnight

recommendedBedtimeEndMins	integer($int32)
End of the recommended bedtime range, in minutes since midnight

preferredActivityTracker	boolean
Whether the device used is the user's preferred activity tracker.

}
```

### DailyNapDTO

```text
DailyNapDTO{
userProfilePK	integer($int64)
deviceId	integer($int64)
calendarDate	string($date)
napTimeSec	integer($int32)
napStartTimestampGMT	string($date-time)
Start of the nap, in UTC.

napEndTimestampGMT	string($date-time)
End of the nap, in UTC.

napFeedback	string
napSource	integer($int32)
Numeric code identifying how the nap was recorded: 0=AUTOMATIC (auto-detected by the device), 1=MANUAL_DEVICE (confirmed manually on the device), 2 = MANUAL_GC.

napStartTimeOffset	integer($int32)
Timezone offset from UTC in minutes.

napEndTimeOffset	integer($int32)
Timezone offset from UTC in minutes.

createTimestampGMT	string($date-time)
updateTimestampGMT	string($date-time)
}
```

### SleepAlignmentDto

```text
SleepAlignmentDto{
description:
DTO for Sleep Alignment. Also known as the Optimal Sleep Window.

userId	integer($int64)
calendarDate	string($date)
deviceId	integer($int64)
isPreferredActivityTracker	boolean
Whether the device used is the user's primary wearable.

sleepNeedBaselineMins	integer($int32)
Duration in minutes of the rhythm sleep window.

optimalSleepWindowStartMins	integer($int32)
Start of the optimal sleep window, specified as signed minutes since midnight

optimalSleepWindowEndMins	integer($int32)
End of the optimal sleep window, specified as signed minutes since midnight

status	string
Status Sleep Alignment feedback.

optimalSleepWindowMidpointMins	integer($int32)
Midpoint of the optimal sleep window, specified as signed minutes since midnight.

lastSleepMidpointMins	integer($int32)
Midpoint of the last sleep window, specified as signed minutes since midnight.

}
UserSettingsDTO
```

### DayOfWeekDTO

```text
DayOfWeekDTO{
dayId	integer($int32)
dayName	string
example: monday, tuesday, wednesday, thursday, friday, saturday, sunday
The name of the day of the week.

sortOrder	integer($int32)
isPossibleFirstDay	boolean
Indicates whether the day is the first day of the week.

}
```

### UnitFormatDTO

```text
UnitFormatDTO{
formatId	integer($int64)
formatKey	string
minFraction	integer($int32)
maxFraction	integer($int32)
groupingUsed	boolean
displayFormat	string
}
```

### HydrationContainer

```text
HydrationContainer{
name	string
volume	integer($int32)
unit	string
}
```

### UserDailyHydrationDTO

```text
UserDailyHydrationDTO{
userId	integer($int64)
calendarDate	string($date)
valueInML	number($double)
The amount of hydration consumed for the day, in milliliters.

goalInML	number($double)
The user's hydration goal for the day, in milliliters.

lastEntryTimestampLocal	string($date-time)
sweatLossInML	number($double)
Hydration lost through sweat for the day, in milliliters.

activityIntakeInML	number($double)
Hydration consumed during activities, in milliliters.

}
```

### StepsDailyStatDTO

```text
StepsDailyStatDTO{
calendarDate	string($date)
totalSteps	integer($int32)
Total steps taken for the day

totalDistance	integer($int32)
Total step distance in meters

stepGoal	integer($int32)
User's step goal for the day

}
```

### MultiValueWellnessChartItemDTO

```text
MultiValueWellnessChartItemDTO{
calendarDate	string($date)
values	{...}
}
```

### UserDailySummaryDto

```text
UserDailySummaryDto{
userProfileId	integer($int64)
displayName	string
totalKilocalories	number($double)
Total calories burned for the day, including basal metabolic rate (BMR) and active calories.

activeKilocalories	number($double)
Active calories burned while moving throughout the day.

bmrKilocalories	number($double)
Basal metabolic rate (BMR) calories burned for the day.

consumedKilocalories	number($double)
Calories consumed for the day.

remainingKilocalories	number($double)
Remaining calories for the day. This is calculated as the user's daily calorie goal minus the calories consumed.

totalSteps	integer($int32)
Total steps taken for the day.

netCalorieGoal	integer($int32)
The user's net calorie goal for the day.

totalDistanceMeters	integer($int32)
Total distance traveled for the day, in meters, including both steps and activity distance.

wellnessDistanceMeters	integer($int32)
Total steps distance traveled for the day, in meters.

userDailySummaryId	integer($int64)
calendarDate	string($date)
uuid	string
dailyStepGoal	integer($int32)
User's daily step goal.

dailyPushesGoal	integer($int32)
User's daily pushes goal.

totalPushDistance	integer($int32)
Total distance traveled for the day through wheelchair pushes, in meters.

totalPushes	integer($int32)
Total wheelchair pushes for the day.

wellnessStartTimeGmt	string($date-time)
GMT timestamp of the first wellness data for the day.

wellnessStartTimeLocal	string($date-time)
Local timestamp of the first wellness data for the day.

wellnessEndTimeGmt	string($date-time)
GMT timestamp of the last wellness data for the day.

wellnessEndTimeLocal	string($date-time)
Local timestamp of the last wellness data for the day.

durationInMilliseconds	integer($int64)
Total duration of wellness data for the day, in milliseconds.

wellnessDescription	string
highlyActiveSeconds	integer($int32)
Total seconds spent while highly active

activeSeconds	integer($int32)
Total seconds spent while active

sedentarySeconds	integer($int32)
Total seconds spent while sedentary

sleepingSeconds	integer($int32)
Total seconds spent while sleeping

includesWellnessData	boolean
Indicates if wellness was uploaded for the day.

includesActivityData	boolean
Indicates if activity was uploaded for the day.

includesCalorieConsumedData	boolean
Indicates if calorie consumed data was provided for the day.

moderateIntensityMinutes	integer($int32)
Total number of moderate intensity minutes for the day.

vigorousIntensityMinutes	integer($int32)
Total number of vigorous intensity minutes for the day.

floorsAscendedInMeters	number($double)
Total floors distance ascended in meters for the day.

floorsDescendedInMeters	number($double)
Total floors distance descended in meters for the day.

floorsAscended	number($double)
Total number of floors ascended for the day.

floorsDescended	number($double)
Total number of floors descended for the day.

intensityMinutesGoal	integer($int32)
User's weekly intensity minutes goal.

userFloorsAscendedGoal	integer($int32)
User's daily floors ascended goal.

minHeartRate	integer($int32)
Minimum heart rate for the day.

maxHeartRate	integer($int32)
Maximum heart rate for the day.

restingHeartRate	integer($int32)
Resting heart rate for the day.

lastSevenDaysAvgRestingHeartRate	integer($int32)
Average resting heart rate for the last seven days.

source	string
Enum:
Array [ 2 ]
averageStressLevel	integer($int32)
Average stress level for the day.

maxStressLevel	integer($int32)
Maximum stress level for the day.

stressDuration	integer($int32)
Total duration stress (low, medium, or high) for the day, in seconds.

restStressDuration	integer($int32)
Total duration of 'rest' stress data, in seconds.

activityStressDuration	integer($int32)
Total duration of 'activity' stress data, in seconds.

uncategorizedStressDuration	integer($int32)
Total duration of 'uncategorized' stress data, in seconds.

totalStressDuration	integer($int32)
Total duration of stress data from across all categories, in seconds.

lowStressDuration	integer($int32)
Total duration of 'low' stress data, in seconds.

mediumStressDuration	integer($int32)
Total duration of 'medium' stress data, in seconds.

highStressDuration	integer($int32)
Total duration of 'high' stress data, in seconds.

stressPercentage	number($double)
Percentage of the day spent in stress (low, medium, or high).

restStressPercentage	number($double)
Percentage of the day spent in 'rest' stress.

activityStressPercentage	number($double)
Percentage of the day spent in 'activity' stress.

uncategorizedStressPercentage	number($double)
Percentage of the day spent in 'uncategorized' stress.

lowStressPercentage	number($double)
Percentage of the day spent in 'low' stress.

mediumStressPercentage	number($double)
Percentage of the day spent in 'medium' stress.

highStressPercentage	number($double)
Percentage of the day spent in 'high' stress.

stressQualifier	string
Enum:
Array [ 9 ]
measurableAwakeDuration	integer($int32)
Measured awake time, in seconds.

measurableAsleepDuration	integer($int32)
Measured asleep time, in seconds.

lastSyncTimestampGMT	string($date-time)
minAvgHeartRate	integer($int32)
Minimum average heart rate for the day, measured over a 2-minute period.

maxAvgHeartRate	integer($int32)
Maximum average heart rate for the day, measured over a 2-minute period.

bodyBatteryChargedValue	integer($int32)
Body Battery charged value for the day.

bodyBatteryDrainedValue	integer($int32)
Body Battery drained value for the day.

bodyBatteryHighestValue	integer($int32)
Body Battery highest value for the day.

bodyBatteryLowestValue	integer($int32)
Body Battery lowest value for the day.

bodyBatteryMostRecentValue	integer($int32)
Body Battery most recent value.

bodyBatteryDuringSleep	integer($int32)
Body Battery charged value during sleep.

bodyBatteryAtWakeTime	integer($int32)
Body Battery value at wake time.

bodyBatteryVersion	number($double)
Body Battery version.

abnormalHeartRateAlertsCount	integer($int32)
Count of abnormal heart rate alerts for the day.

averageSpo2	number($double)
Average Pulse Ox value for the day.

lowestSpo2	integer($int32)
Lowest Pulse Ox value for the day.

latestSpo2	integer($int32)
Latest Pulse Ox value for the day.

latestSpo2ReadingTimeGmt	string($date-time)
GMT timestamp of the latest Pulse Ox reading for the day.

latestSpo2ReadingTimeLocal	string($date-time)
Local timestamp of the latest Pulse Ox reading for the day.

averageMonitoringEnvironmentAltitude	number($double)
Average Pulse Ox Acclimation for the day.

bodyBatteryDynamicFeedbackEvent	{...}
endOfDayBodyBatteryDynamicFeedbackEvent	{...}
bodyBatteryActivityEventList	[...]
isJetLagDay	boolean
Indicates if the user is experiencing jet lag on this day.

jetLagTripName	string
Name of the trip associated with jet lag, if applicable.

hydrationValueInML	number($double)
The amount of hydration consumed for the day, in milliliters.

hydrationGoalInML	number($double)
The user's hydration goal for the day, in milliliters.

avgWakingRespirationValue	number($double)
Average respiration value while awake.

highestRespirationValue	number($double)
Highest respiration value for the day.

lowestRespirationValue	number($double)
Lowest respiration value for the day.

latestRespirationValue	number($double)
Latest respiration value for the day.

latestRespirationTimeGMT	string($date-time)
respirationAlgorithmVersion	integer($int32)
Version of the respiration algorithm used.

}
```

### BodyBatteryDynamicFeedbackEventDTO

```text
BodyBatteryDynamicFeedbackEventDTO{
eventTimestampGmt	string($date-time)
bodyBatteryLevel	string
Body Battery level (0-100).

feedbackShortType	string
feedbackLongType	string
}
```

### BodyBatteryActivityEventDTO

```text
BodyBatteryActivityEventDTO{
eventType	string
The type of Body Battery event - 'ACTIVITY', 'SLEEP', 'STRESS', 'RECOVERY', or 'NAP'.

eventStartTimeGmt	string($date-time)
Start time of the event, in UTC.

timezoneOffset	integer($int32)
Timezone offset from UTC, in ms.

durationInMilliseconds	integer($int64)
bodyBatteryImpact	integer($int32)
feedbackType	string
Type of feedback/insight associated with this event.

shortFeedback	string
}
```

### ApiDocumentListUserDailySummaryV2DTO

```text
ApiDocumentListUserDailySummaryV2DTO{
data	[...]
}
```

### UserDailySummaryV2DTO

```text
UserDailySummaryV2DTO{
description:
A user's daily summary. Related fields are grouped together (see each nested object's schema for more details). Unless otherwise noted, the following conventions are observed:

Dates and timestamps are given as unqualified (no timezone) ISO-8601 strings; durations are given as integer milliseconds.
Decimal values are rounded to 2 decimal places.
uuid	string($uuid)
example: 123e4567-e89b-12d3-a456-426655440000
userProfilePk	integer($int64)
example: 987654321
calendarDate	string($date)
example: 2023-10-09
source	string
example: garmin
The programmatic source of this summary. Values are case insensitive.

Enum:
Array [ 2 ]
includesWellnessData	boolean
Whether or not wellness data is reflected in this user daily summary.

includesActivityData	boolean
Whether or not activity data is reflected in this user daily summary.

wellnessChronology	WellnessChronologyV2DTO{...}
movement	MovementV2DTO{...}
example: {"steps":{"goal":10000,"value",5000,"distanceInMeters",3810.0},"pushes":{"goal":2500,"value":1250,"distanceInMeters":316.8},"floorsAscended":{"goal":10,"value":5,"distanceInMeters":15.24},"floorsDescended":{"value":3,"distanceInMeters":9.144}}
calories	CaloriesV2DTO{...}
heartRate	HeartRateV2DTO{...}
intensityMinutes	IntensityMinutesV2DTO{...}
stress	StressV2DTO{...}
bodyBattery	BodyBatteryV2DTO{...}
hydration	HydrationV2DTO{...}
respiration	RespirationV2DTO{...}
pulseOx	PulseOxV2DTO{...}
jetLag	JetLagV2DTO{...}
}
```

### WellnessChronologyV2DTO

```text
WellnessChronologyV2DTO{
description:
Contains chronological metadata about the daily summary

startTimestampGmt	string($date-time)
UTC/GMT timestamp of the first wellness data.

startTimestampLocal	string($date-time)
User's local timestamp of the first wellness data.

endTimestampGmt	string($date-time)
UTC/GMT timestamp of the last wellness data.

endTimestampLocal	string($date-time)
User's local timestamp of the last wellness data.

totalDurationInMillis	integer($int32)
example: 57600000
Total duration of wellness data.

}
```

### MovementV2DTO

```text
MovementV2DTO{
description:
Contains information about movement (i.e.: steps, wheelchair pushes, and floors ascended/descended). Fractional values for floors ascended/descended are resolved by flooring to the nearest lower integer.

steps	MovementValueV2DTO{...}
pushes	MovementValueV2DTO{...}
floorsAscended	MovementValueV2DTO{...}
floorsDescended	MovementValueV2DTO{...}
}
example: {"steps":{"goal":10000,"value",5000,"distanceInMeters",3810.0},"pushes":{"goal":2500,"value":1250,"distanceInMeters":316.8},"floorsAscended":{"goal":10,"value":5,"distanceInMeters":15.24},"floorsDescended":{"value":3,"distanceInMeters":9.144}}
```

### MovementValueV2DTO

```text
MovementValueV2DTO{
description:
Contains information about movement (e.g.: steps, wheelchair pushes, floors ascended/descended).

goal	integer($int32)
example: 10000
User's daily goal for this type of movement.

value	integer($int32)
example: 5000
Actual value for this type of movement for the day.

distanceInMeters	number($double)
example: 3810
The distance traveled for the day as part of this type of movement. Given in meters.

}
```

### CaloriesV2DTO

```text
CaloriesV2DTO{
description:
Contains information about calories burned and consumed.

burnedResting	integer($int32)
example: 1000
Basal metabolic rate (BMR) calories burned for the day.

burnedActive	integer($int32)
example: 500
Active calories burned for the day.

burnedTotal	integer($int32)
example: 1500
Total calories burned for the day.

consumedGoal	integer($int32)
example: 2000
User goal for daily consumed calories (this can change day-to-day).

consumedValue	integer($int32)
example: 1200
Calories consumed for the day.

consumedRemaining	integer($int32)
example: 1300
Remaining calories the user should consume to reach their goal for the day, adjusted upwards for any burned active calories (e.g.: consumedGoal - consumedValue + burnedActive). If negative, the user has already exceeded their goal.

}
```

### HeartRateV2DTO

```text
HeartRateV2DTO{
description:
Contains information about heart rate. Values are given in beats-per-minute (BPM).

minValue	integer($int32)
example: 60
Minimum 2-minute average heart rate for the day, or the absolute minimum if no 2-minute average is available.

maxValue	integer($int32)
example: 180
Maximum 2-minute average heart rate for the day, or the absolute maximum if no 2-minute average is available.

restingValue	integer($int32)
example: 100
Resting heart rate for the day, or the absolute minimum if no resting value is available.

alertCount	integer($int32)
example: 0
Number of abnormal heart rate alerts for the day.

}
```

### IntensityMinutesV2DTO

```text
IntensityMinutesV2DTO{
description:
Contains information about intensity minutes.

goal	integer($int32)
example: 150
User's weekly intensity minutes goal.

moderate	integer($int32)
example: 30
Moderate intensity minutes for the day.

vigorous	integer($int32)
example: 15
Vigorous intensity minutes for the day.

}
```

### StressV2DTO

```text
StressV2DTO{
description:
Contains information about stress. Garmin stress levels are given on a scale of 0 to 100.

avgLevel	integer($int32)
example: 50
Average Garmin stress level.

maxLevel	integer($int32)
example: 100
Maximum Garmin stress level.

restProportion	number($double)
example: 0.47
Proportion of time spent in rest.

activityProportion	number($double)
example: 0.06
Proportion of time spent in activity stress.

uncategorizedProportion	number($double)
example: 0.03
Proportion of time spent in uncategorized stress.

lowStressProportion	number($double)
example: 0.22
Proportion of time spent in low stress.

mediumStressProportion	number($double)
example: 0.19
Proportion of time spent in medium stress.

highStressProportion	number($double)
example: 0.03
Proportion of time spent in high stress.

qualifier	string
example: very_stressful
Stress qualifier/descriptor for the day.

Enum:
Array [ 9 ]
totalDurationInMillis	integer($int32)
example: 57600000
Total duration of stress data.

restDurationInMillis	integer($int32)
example: 27000000
Duration of rest.

activityDurationInMillis	integer($int32)
example: 3600000
Duration of activity stress.

uncategorizedDurationInMillis	integer($int32)
example: 1800000
Duration of uncategorized stress.

lowStressDurationInMillis	integer($int32)
example: 12600000
Duration of low stress.

mediumStressDurationInMillis	integer($int32)
example: 10800000
Duration of medium stress.

highStressDurationInMillis	integer($int32)
example: 1800000
Duration of high stress.

}
```

### BodyBatteryV2DTO

```text
BodyBatteryV2DTO{
description:
Contains information about body battery. All values are given on a scale 5 to 100. The term "endOfDay" in this object refers to the last value before the user's sleep period; in other words, the value at the end of their "waking day", not the "calendar day".

minValue	integer($int32)
maximum: 100
minimum: 5
example: 10
Minimum Body Battery value for the day.

maxValue	integer($int32)
maximum: 100
minimum: 5
example: 85
Maximum Body Battery value for the day.

chargedValue	integer($int32)
maximum: 100
minimum: 5
example: 80
Increase in Body Battery over the day.

drainedValue	integer($int32)
maximum: 100
minimum: 5
example: 20
Decrease in Body Battery over the day.

latestValue	integer($int32)
maximum: 100
minimum: 5
example: 60
Latest Body Battery value.

endOfDayValue	integer($int32)
maximum: 100
minimum: 5
example: 20
Latest Body Battery value prior to sleep.

featureVersion	string
example: 2.0
The Body Battery feature version for the user's device.

dynamicFeedbackEvent	BodyBatteryDynamicFeedbackEventDTO{...}
endOfDayDynamicFeedbackEvent	BodyBatteryDynamicFeedbackEventDTO{...}
activityEvents	[...]
}
```

### BodyBatteryActivityEventV2DTO

```text
BodyBatteryActivityEventV2DTO{
eventType	string
eventStartTimeGmt	string($date-time)
eventStartTimeLocal	string($date-time)
bodyBatteryImpact	integer($int32)
feedbackType	string
shortFeedback	string
deviceId	integer($int64)
activityName	string
activityType	string
activityId	integer($int64)
durationInMillis	integer($int32)
example: 3600000
}
```

### HydrationV2DTO

```text
HydrationV2DTO{
description:
Contains information about hydration. All values are given in milliliters (ml).

goalInMl	integer($int32)
example: 2000
User's daily hydration goal (this can change day-to-day).

goalInFractionalMl	number($double)
example: 2000.4321
User's daily hydration goal (this can change day-to-day). Due to unique client requirements for converting and displaying hydration goals and values, this value is NOT rounded.

consumedInFractionalMl	number($double)
example: 1000.4321
Actual water consumed for the day. Due to unique client requirements for converting and displaying hydration goals and values, this value is NOT rounded.

}
```

### RespirationV2DTO

```text
RespirationV2DTO{
description:
Contains information about respiration. All values are given in breaths-per-minute.

avgValue	integer($int32)
example: 15
Average respiration rate for the day.

maxValue	integer($int32)
example: 20
Maximum respiration rate for the day.

minValue	integer($int32)
example: 10
Minimum respiration rate for the day.

latestValue	integer($int32)
example: 18
Latest respiration rate for the day.

latestTimestampGmt	string($date-time)
UTC/GMT timestamp of the latest reading (no local equivalent is available).

algorithmVersion	integer($int32)
example: 100
Respiration algorithm used.

}
```

### PulseOxV2DTO

```text
PulseOxV2DTO{
description:
Contains information about pulse oximetry. All values are given as percentages 0 to 100.

avgValue	integer($int32)
maximum: 100
minimum: 0
example: 95
Average pulse ox value for the day.

minValue	integer($int32)
maximum: 100
minimum: 0
example: 90
Minimum pulse ox value for the day.

latestValue	integer($int32)
maximum: 100
minimum: 0
example: 94
Latest pulse ox value for the day.

latestTimestampGmt	string($date-time)
UTC/GMT timestamp of the latest reading.

latestTimestampLocal	string($date-time)
User's local timestamp of the latest reading.

avgAltitudeInMeters	number($double)
example: 327
Average monitoring environment altitude for the day. Given as meters above mean sea level.

}
```

### JetLagV2DTO

```text
JetLagV2DTO{
tripName	string
Name of the trip associated with jet lag, if applicable.

}
```

### DateWeightDTO

```text
DateWeightDTO{
description:
Represents a user's weight and body composition measurements for a date.

date	string($date-time)
User's local date associated with the weight measurement.

calendarDate	string
pattern: 2022-08-10
User's Local Calendar date associated with the weight measurement. DateFormat: yyyy-MM-dd

weight	number($double)
Weight measurement in kilograms.

bmi	number($double)
Body mass index measurement.

bodyFat	number($double)
Body fat measurement.

bodyWater	number($double)
Body water measurement.

boneMass	integer($int32)
Bone mass measurement.

muscleMass	integer($int32)
Muscle mass measurement.

physiqueRating	integer($int32)
Physique rating.

visceralFat	integer($int32)
Visceral fat measurement.

metabolicAge	number($double)
Metabolic age measurement.

timestampGMT	string($date-time)
GMT timestamp of the weight measurement. DateFormat: yyyy-MM-dd'T'HH:mm:ss.SSSZ

weightDelta	number($double)
Difference from the previous weight measurement.

}
```

### WeightRangeDTO

```text
WeightRangeDTO{
description:
Represents a range of weight summaries, including daily summaries, the total average, and adjacent weights.

dailyWeightSummaries	[...]
totalAverage	{...}
previousDateWeight	{...}
nextDateWeight	{...}
}
```

### DailyWeightSummary

```text
DailyWeightSummary{
description:
Represents a summary of weight measurements for a specific date.

summaryDate	string
pattern: 2022-08-10
Calendar date represented by this summary. Date YYYY-MM-DD format

numOfWeightEntries	integer($int32)
Number of weight entries recorded for this date.

minWeight	number($double)
Minimum weight recorded for this date.

maxWeight	number($double)
Maximum weight recorded for this date.

latestWeight	{...}
allWeightMetrics	[...]
}
```

### WeightAverageDTO

```text
WeightAverageDTO{
description:
Average weight and body composition measurements over a date range.

from	string($date-time)
Start date of the range for which the averages are calculated. DateFormat: yyyy-MM-dd'T'HH:mm:ss.SSSZ

until	string($date-time)
End date of the range for which the averages are calculated. DateFormat: yyyy-MM-dd'T'HH:mm:ss.SSSZ

weight	number($double)
Average weight over the date range.

bmi	number($double)
Average Body Mass Index (BMI) over the date range.

bodyFat	number($double)
Average body fat percentage over the date range.

bodyWater	number($double)
Average body water percentage over the date range.

boneMass	integer($int32)
Average bone mass over the date range.

muscleMass	integer($int32)
Average muscle mass over the date range.

physiqueRating	integer($int32)
Average physique rating over the date range.

visceralFat	integer($int32)
Average visceral fat over the date range.

metabolicAge	number($double)
Average metabolic age over the date range.

}
```

### BodyBatteryDailyReportDTO

```text
BodyBatteryDailyReportDTO{
date	string($date)
Calendar date this Body Battery report is for.

charged	integer($int32)
Amount of Body Battery charged during the day, on the 0-100 Body Battery scale.

drained	integer($int32)
Amount of Body Battery drained during the day, on the 0-100 Body Battery scale.

startTimestampGMT	string($date-time)
Start of the reporting window, in UTC

endTimestampGMT	string($date-time)
End of the reporting window, in UTC.

startTimestampLocal	string($date-time)
Start of the reporting window, in the user's local timezone.

endTimestampLocal	string($date-time)
End of the reporting window, in the user's local timezone.

bodyBatteryValuesArray	[...]
bodyBatteryValueDescriptorDTOList	[...]
bodyBatteryDynamicFeedbackEvent	BodyBatteryDynamicFeedbackEventDTO{...}
bodyBatteryActivityEvent	[...]
endOfDayBodyBatteryDynamicFeedbackEvent	BodyBatteryDynamicFeedbackEventDTO{...}
}
```

### BodyBatteryValueDescriptorDTO

```text
BodyBatteryValueDescriptorDTO{
bodyBatteryValueDescriptorIndex	integer($int32)
Column index into each row of bodyBatteryValuesArray that this descriptor describes.

bodyBatteryValueDescriptorKey	string
Name of the column described by this descriptor: timestamp, bodyBatteryLevel, bodyBatteryStatus, or bodyBatteryVersion.

}
```

### DailySpO2AndAcclimationDTO

```text
DailySpO2AndAcclimationDTO{
userProfilePK	integer($int64)
calendarDate	string
pattern: 2022-08-10
startTimestampGMT	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

endTimestampGMT	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

startTimestampLocal	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

endTimestampLocal	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

sleepStartTimestampGMT	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

sleepEndTimestampGMT	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

sleepStartTimestampLocal	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

sleepEndTimestampLocal	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

tomorrowSleepStartTimestampGMT	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

tomorrowSleepEndTimestampGMT	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

tomorrowSleepStartTimestampLocal	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

tomorrowSleepEndTimestampLocal	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator!

averageSpO2	number($double)
Average blood oxygen saturation (SpO2) percentage measured during the reporting window.

lowestSpO2	integer($int32)
Lowest blood oxygen saturation (SpO2) percentage measured during the reporting window.

lastSevenDaysAvgSpO2	number($double)
Average SpO2 percentage over the trailing 7 days, used as a baseline for acclimation comparison.

latestSpO2	integer($int32)
Most recent SpO2 reading percentage.

latestSpO2TimestampGMT	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator! Timestamp, in UTC, of the most recent SpO2 reading.

latestSpO2TimestampLocal	string
pattern: 2022-08-10T09:47:59\.031
iso 8601 timestamp without GMT offset or 'Z' indicator! Timestamp, in the user's local timezone, of the most recent SpO2 reading.

avgSleepSpO2	number($double)
avgTomorrowSleepSpO2	number($double)
spO2SingleValuesDescriptorList	[...]
spO2SingleValues	[...]
spO2HourlyAveragesDescriptorList	[...]
spO2HourlyAverages	[...]
monitoringEnvironmentValuesDescriptorList	[...]
monitoringEnvironmentValues	[...]
}
```

### SPO2ValueDescriptorDTO

```text
SPO2ValueDescriptorDTO{
spo2ValueDescriptorIndex	integer($int32)
spo2ValueDescriptorKey	string
}
```

### SPO2AcclimationValueDescriptorDTO

```text
SPO2AcclimationValueDescriptorDTO{
spo2ValueDescIndex	integer($int32)
spo2ValueDescKey	string
Name of the column described: timestamp, spo2Level, or monitoringEnvironmentLevel.

}
```

### MonitoringEnvironmentValueDescriptorDTO

```text
MonitoringEnvironmentValueDescriptorDTO{
monEnvValueDescIndex	integer($int32)
monEnvValueDescKey	string
Name of the column described: timestamp or monitoringEnvironmentLevel.

}
```

### DailyHeartRateDTO

```text
DailyHeartRateDTO{
userProfilePK	integer($int64)
calendarDate	ConnectDate{...}
startTimestampGMT	ConnectTimestamp{...}
endTimestampGMT	ConnectTimestamp{...}
startTimestampLocal	ConnectTimestamp{...}
endTimestampLocal	ConnectTimestamp{...}
maxHeartRate	integer($int32)
minHeartRate	integer($int32)
restingHeartRate	integer($int32)
lastSevenDaysAvgRestingHeartRate	integer($int32)
abnormalHrThresholdValue	integer($int32)
High heart rate threshold, above which readings are flagged as abnormal.

lowAbnormalHrThresholdValue	integer($int32)
Low heart rate threshold, below which readings are flagged as abnormal.

abnormalHRValuesArray	[...]
heartRateValueDescriptors	[...]
heartRateValues	[...]
}
```

### HeartRateValueDescriptorDTO

```text
HeartRateValueDescriptorDTO{
index	integer($int32)
key	string
Name of the column described: timestamp or heartrate.

}
```

### WellnessActivitySummaryDTO

```text
WellnessActivitySummaryDTO{
userProfilePk	integer($int64)
The primary key of the user profile this summary belongs to.

activityUuid	{...}
calendarDate	{...}
rulePK	integer($int64)
The value belonging to the access control rule associated with this activity summary. 1=public, 2=private, 3=shared with subscribers, 4=shared with group.

activityName	string
The name of the wellness activity.

notes	string
Additional notes about the wellness activity.

wellnessActivityType	string
The type of the wellness activity.

Enum:
Array [ 2 ]
startTimestampGMT	{...}
endTimestampGMT	{...}
startTimestampLocal	{...}
endTimestampLocal	{...}
summaryTypeDataList	[...]
timeInZoneList	[...]
deviceMetaData	{...}
}
```

### SummaryTypeDataDTO

```text
SummaryTypeDataDTO{
description:
A summary of a specific type of data associated with the wellness activity. Includes the type of data, the minimum value, maximum value, and average value.

summaryType	string
Enum:
Array [ 7 ]
minValue	number($double)
maxValue	number($double)
avgValue	number($double)
}
```

### TimeInZoneDTO

```text
TimeInZoneDTO{
description:
A summary of the time spent in a specific zone, including which zone, the duration in ms spent in the zone, and the lower boundary of the zone.

zoneNumber	integer($int32)
Zone number.

millisInZone	integer($int32)
Total time, in milliseconds, spent in this zone during the activity.

zoneLowBoundary	integer($int32)
Lower boundary value defining this zone.

}
```

### DeviceMetaDataDTO

```text
DeviceMetaDataDTO{
description:
Metadata about a device, including the device ID, type ID, version ID, version string, and name.

deviceId	integer($int64)
deviceTypeId	integer($int64)
Identifier of the device type/model.

deviceVersionId	integer($int64)
Identifier of the specific device firmware/version record.

deviceVersion	string
Human-readable version string of the device firmware.

deviceName	string
Display name of the device.

}
```

### GarminUUID

```text
GarminUUID{
leastSignificantBits	integer($int64)
mostSignificantBits	integer($int64)
baseUUID	string($uuid)
}
```
