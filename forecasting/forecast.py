
def calculate_forecasts(courses, historical, interests):

    forecasts = []

    for course in courses:

        course_id = course[0]

        historical_count = historical.get(course_id, 0)
        interest_count = interests.get(course_id, 0)

        predicted_demand = (
            (0.7 * historical_count) +
            (0.3 * interest_count)
        )

        predicted_demand = int(predicted_demand + 0.5)

        historical_support = min(
            historical_count / 100,
            1.0
        )

        interest_support = min(
            interest_count / 100,
            1.0
        )

        confidence = (
            (0.5 * historical_support) +
            (0.5 * interest_support)
        )

        confidence = round(confidence, 4)

        if predicted_demand >= 50:
            category = "HIGH"
        elif predicted_demand >= 20:
            category = "MEDIUM"
        else:
            category = "LOW"

        forecast = (
            course_id,
            historical_count,
            interest_count,
            predicted_demand,
            confidence,
            category
        )

        forecasts.append(forecast)

    return forecasts
