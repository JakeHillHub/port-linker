import pydux
from state.reducer import reducer

store = pydux.create_store(reducer)
