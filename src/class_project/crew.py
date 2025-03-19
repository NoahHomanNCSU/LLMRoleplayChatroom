import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class CocktailPartyChatbot():
    """CocktailPartyChatbot crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def topic_generator(self) -> Agent:
        return Agent(config=self.agents_config['topic_generator'], verbose=True)

    @agent
    def persona(self) -> Agent:
        return Agent(config=self.agents_config['persona'])

    @agent
    def critic(self) -> Agent:
        return Agent(config=self.agents_config['critic'])

    @task
    def generate_topic(self) -> Task:
        """Generate a conversation topic and save it."""
        return Task(config=self.tasks_config['generate_topic'])

    @task
    def persona_response(self) -> Task:
        """Generate a persona response based on the topic."""
        return Task(config=self.tasks_config['persona_response'])

    
    # @task
    # def critique_response(self) -> Task:
    #     """Critique the persona's response and save it."""
    #     return Task(config=self.tasks_config['critique_response'])

    # @task
    # def refine_response(self) -> Task:
    #     """Refine the persona's response based on the critique."""
    #     return Task(config=self.tasks_config['refine_response'])

    @crew
    def crew(self) -> Crew:
        """Creates the CocktailPartyChatbot crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
