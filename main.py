from src.react_agent.logging import get_logger
from src.react_agent.learning_loop import git_triggered_learning_loop, memory_ledger_learning_loop

def main():
    """
    The main function of the application.
    """
    # Initialize the logger
    logger = get_logger()
    logger.info("Application started.")

    # Initialize the learning loops
    git_triggered_learning_loop("Initial commit")
    memory_ledger_learning_loop()

    logger.info("Learning loops initialized.")

    # Main application logic goes here
    print("Hello from npt-knowing-2!")

    logger.info("Application finished.")

if __name__ == "__main__":
    main()
