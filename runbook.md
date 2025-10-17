**Key Rotation** 

For key rotation, since I am running this locally I don’t have a mechanism for key rotation. However, all of my keys are located in my .env 

—-------------------------------------------------------------------


LANGCHAIN_TRACING_V2=

LANGSMITH_API_KEY=

LANGCHAIN_PROJECT=

GROQ_MODEL=

HASH_SECRET_KEY=

ENCRYPTION_ON=


—-------------------------------------------------------------------

So to rotate keys you can manually change them. 

However, if I were to implement this in product there are 2 approaches that come to mind based on past experiences: 

(1) Grafiniti is deployed with Netlify. They use Doppler for key storage and rotation. 
(2) Another approach is AWS. AWS has multiple in-built key storage and rotational mechanisms, including KMS and Secrets Manager. 


**Tune Prompts** 

The system prompt itself is written in email_agent_parser.py and you can always change it. 

I also have a main in that file itself that you can invoke if you want to test prompts in the IDE you can run `python email_agent_parser,py` 

However, for a more visual friendly way I have keys in the .env for 
LANGCHAIN_TRACING, LANGSMITH_API_KEY, and LANGCHAIN_PROJECT. Also I have a langgraph.json file. What all this allows is that you can use the langgraph dev, like how this guy did it: `https://www.youtube.com/watch?v=Mi1gSlHwZLM&t=468s` 
Look at time 1:10. 

In this interface you can change prompts and see what the agent does without having to run the entire app. Its a great place for rapid development and testing. 

**Debug Bad Parse** 

I touched on the tune prompt section about how you can go into langgraph studio and look at the output of the agent. That is one way of debugging a specific prompt. 

Another way is to create a for-loop in the main. 

I have sample_inputs inside the `email_agent_parser.py`. You can always modify it with your own input see what it does. That is a good way for checking 10 different prompts without having to enter it in manually try different scenarios to see where the agent trips up
