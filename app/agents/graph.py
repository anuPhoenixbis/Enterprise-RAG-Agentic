from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import AgentState
from app.agents.nodes.planner import planner_node
from app.agents.nodes.retreiver import retrieve_node
from app.agents.nodes.responder import generate_node

# initialize the graph
workflow = StateGraph(AgentState)

#define the nodes
workflow.add_node("planner",planner_node)
workflow.add_node("retriever",retrieve_node)
workflow.add_node("responder",generate_node)

#define the edges and routing logic
def route_planner(state: AgentState):
    #routes to workflow based on planner's decision
     if state["current_query"] == "CONVERSATIONAL":
         return "responder" #gives the response
     return "retriever"#gives the retrieved response

workflow.set_entry_point("planner") #workflow will start from planner

#conditional edges: planner -> router -> (retriever or responder)
workflow.add_conditional_edges(
    "planner",
    route_planner,
    {
        "retriever": "retriever",
        "responder": "responder",
    }
)

workflow.add_edge("retriever", "responder") #retriever -> responder
workflow.add_edge("responder", END) #after responder END of graph

#memory upgrade
#memory saver allows the agent to remember convos based on thread_id
checkpointer = MemorySaver()

#compile the graph memory
rag_agent = workflow.compile(checkpointer)