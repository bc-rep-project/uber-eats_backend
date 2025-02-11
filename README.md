# UberEats Clone Backend

This is the backend service for the UberEats clone project, built with Flask and MongoDB.

## Tech Stack

- **Framework**: Flask
- **Database**: MongoDB
- **Authentication**: JWT
- **Payment Processing**: Stripe
- **Real-time Updates**: WebSocket (Flask-SocketIO)
- **Testing**: pytest

## Prerequisites

- Python 3.8+
- MongoDB 5+
- Redis (optional, for future use)

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Update the `.env` file with your configuration:
- MongoDB connection string
- JWT secrets
- Stripe API keys
- Other service configurations

5. Initialize the database:
```bash
python src/config/init_db.py
```

## Project Structure

```
backend/
├── src/
│   ├── config/          # Configuration files
│   ├── controllers/     # Request handlers
│   ├── models/          # Database models
│   ├── routes/          # API routes
│   ├── services/        # Business logic
│   ├── middleware/      # Custom middleware
│   └── utils/          # Helper functions
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── fixtures/       # Test fixtures
├── docs/              # Documentation
└── requirements.txt   # Python dependencies
```

## Available Scripts

- Start development server:
```bash
python src/app.py
```

- Run tests:
```bash
pytest
```

- Run tests with coverage:
```bash
pytest --cov=src tests/
```

## API Documentation

The API documentation is available at `/docs/API_DOCUMENTATION.md`. Key endpoints include:

### Authentication
- `POST /api/auth/register`: Register new user
- `POST /api/auth/login`: User login
- `GET /api/auth/me`: Get current user

### Orders
- `POST /api/orders`: Create order
- `GET /api/orders`: List orders
- `GET /api/orders/<id>`: Get order details
- `PUT /api/orders/<id>/status`: Update order status

### Restaurant Management
- `GET /api/restaurant/settings`: Get restaurant settings
- `PUT /api/restaurant/settings`: Update restaurant settings
- `POST /api/restaurant/menu-items`: Create menu item
- `GET /api/restaurant/analytics`: Get restaurant analytics

## WebSocket Events

Real-time events are handled through WebSocket connections:

- `order_status`: Order status updates
- `new_order`: New order notifications
- `payment_update`: Payment status changes
- `delivery_update`: Delivery tracking updates

## Testing

The project uses pytest for testing. Tests are organized into:

- Unit tests: Testing individual components
- Integration tests: Testing component interactions
- End-to-end tests: Testing complete workflows

Run specific test categories:
```bash
pytest tests/unit/
pytest tests/integration/
pytest -m "slow"  # Run slow tests
```

## Development Guidelines

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Document functions and classes

2. **Git Workflow**
   - Create feature branches from `develop`
   - Use conventional commits
   - Write descriptive PR descriptions

3. **Testing**
   - Write tests for new features
   - Maintain test coverage above 80%
   - Use meaningful test names

4. **Security**
   - Validate all inputs
   - Use parameterized queries
   - Keep dependencies updated

## Deployment

The backend is deployed on Render.com. Deployment is automated through GitHub Actions:

1. **Staging Environment**
   - Automatic deployment on merge to `develop`
   - Environment: `staging`
   - URL: `https://api-staging.example.com`

2. **Production Environment**
   - Manual deployment from `main`
   - Environment: `production`
   - URL: `https://api.example.com`

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 