curl -X POST "http://localhost:8000/api/v1/auth/register" \
-H "Content-Type: application/json" \
-d '{
  "email": "admin@example.com",
  "password": "password1234"
}'