# Import all the models, so that Base has them before being
# imported by Alembic
from mindloom.db.base_class import Base # noqa

# Import your models here after they are created
# Example:
from mindloom.app.models.user import User # noqa
from mindloom.app.models.agent import AgentORM # noqa # Import the SQLAlchemy Agent model
from mindloom.app.models.team import TeamORM # noqa # Import the SQLAlchemy Team model
from mindloom.app.models.run import RunORM # noqa # Import the SQLAlchemy Run model
from mindloom.app.models.agent import AgentScheduleORM # noqa # Import the SQLAlchemy AgentSchedule model
from mindloom.app.models.agent import AgentVariableORM # noqa # Import the SQLAlchemy AgentVariable model
from mindloom.app.models.run import RunLogORM # noqa # Import the SQLAlchemy RunLog model
from mindloom.app.models.run import RunArtifactORM # noqa # Import the SQLAlchemy RunArtifact model
