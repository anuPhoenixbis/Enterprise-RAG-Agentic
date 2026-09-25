#to maintain the flow of agents b/w the nodes we need a state to identify the
#state we are currently in
from typing import TypedDict,List, Annotated
import operator

class AgentState(TypedDict):
    #use the annotated with operator.add ensures that msgs are appended
    #to the history rather than replaced
    messages: Annotated[List[dict], operator.add]
    # 4 kinds of messages are being handled here:
    #AI, Human, Tool(where we tell what to do or behave), system
    current_query: str #current prompt of the user
    documents: List[str] #docs given
    plan: List[str]# to decide if the convo is relevant or not
    status: str #current node
    final_answer: str #answer given