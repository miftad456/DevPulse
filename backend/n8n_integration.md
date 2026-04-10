# Job Matching with n8n

In devPulse, n8n is responsible for orchestrating job scraping and triggering job matching logic using DevPulse's MongoDB. 

## MongoDB Data Structure for Matching
With the latest Onboarding update, User documents now store preferences that can be directly queried by n8n.
Inside the `users` collection, each developer who completed onboarding will look similar to this:

```json
{
  "_id": ObjectId("..."),
  "username": "johndoe",
  "email": "johndoe@example.com",
  "job_role": "Backend Developer",
  "experience_level": "Mid",
  "job_type": "Remote",
  "skills": ["Python", "FastAPI", "MongoDB"],
  "onboarding_completed": true
}
```

## Creating Indexes for Fast Matching
To make n8n searches instantaneous, run this command in your MongoDB shell or Compass:
```javascript
db.users.createIndex({ "job_role": 1, "experience_level": 1, "skills": 1 })
```

## How to Query from n8n
Inside an **n8n MongoDB node** (Operation: `Find Many`), you can query users matching a specific job perfectly. 

### Scenario: You just scraped a Junior React Frontend job
Construct the JSON query for the `users` collection:
```json
{
  "onboarding_completed": true,
  "job_role": "Frontend Developer",
  "experience_level": { "$in": ["Junior", "Entry Level"] },
  "skills": { "$elemMatch": { "$eq": "React" } },
  "job_type": { "$in": ["Remote", "Hybrid"] }
}
```

This returns all developer documents that match the job criteria. n8n can then iterate over these documents, extract the `email`, and use an **Email node** or **Telegram node** to notify the matched developers!

---

## Job Ingestion & Webhook Triggers
As of Phase 2, DevPulse has a built-in Matching Engine. 

### 1. Pushing scraped jobs to DevPulse
When your n8n workflow scrapes a job from LinkedIn or Indeed, push it to DevPulse using the `HTTP Request` node:
- **Method**: `POST`
- **URL**: `YOUR_BACKEND_URL/jobs/ingest`
- **Headers**: `x-api-key: <N8N_API_KEY>`
- **Body**:
```json
{
  "title": "Senior AI Engineer",
  "company": "OpenAI",
  "job_type": "remote",
  "experience_level": "senior",
  "tech_stack": ["Python", "TensorFlow", "FastAPI"],
  "description": "...",
  "source": "linkedin",
  "url": "https://linkedin.com/jobs/..."
}
```

### 2. Receiving Matches (Backend -> n8n)
DevPulse will automatically score and match ingested jobs against user preferences. When it finds matches, it triggers a webhook in n8n.
- Create a **Webhook Node** in n8n listening for `POST` requests.
- Set your DevPulse `.env` variable `N8N_WEBHOOK_URL` to match this n8n node URL.
- The payload n8n will receive from DevPulse looks like this:

```json
{
  "user": {
    "id": "...",
    "email": "dev@email.com",
    "username": "superdev"
  },
  "jobs": [
    {
      "title": "Senior AI Engineer",
      "company": "OpenAI",
      "url": "https://...",
      "match_score": 6,
      "source": "linkedin"
    }
  ]
}
```

By keeping all email and Telegram integrations directly inside n8n, the backend stays lean and n8n handles the dynamic communication templates!
