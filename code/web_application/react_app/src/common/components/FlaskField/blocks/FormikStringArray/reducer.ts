/**
 * Autocomplete reducer
 */

// An enum with all the types of actions to use in our reducer
export enum AutocompleteActionKind {
  SET_CUR_INPUT = "SET_CUR_INPUT",
  SET_AUTO_ARR = "SET_AUTO_ARR",
  SET_SHOW = "SET_SHOW",
  SET_CUR_SELECTED = "SET_CUR_SELECTED",
  ADD_CUR_SELECTED = "ADD_CUR_SELECTED",
  REMOVE_CUR_SELECTED = "REMOVE_CUR_SELECTED",
}

// An interface for our actions
interface AutocompleteAction {
  type: AutocompleteActionKind;
  payload?: any;
}

// An interface for our state
interface AutocompleteState {
  curInput: string;
  autoArr: string[];
  curSelected: number;
  show: boolean;
}

export const autocompleteInitialState: AutocompleteState = {
  curInput: "",
  autoArr: [],
  curSelected: 0,
  show: false,
};

// Our reducer function that uses a switch statement to handle our actions
export function autocompleteReducer(
  state: AutocompleteState,
  action: AutocompleteAction
): AutocompleteState {
  const { type, payload } = action;
  switch (type) {
    // * Manipulated currently selected autocomplete
    case AutocompleteActionKind.ADD_CUR_SELECTED:
      return {
        ...state,
        curSelected: state.curSelected + 1,
      };
    case AutocompleteActionKind.REMOVE_CUR_SELECTED:
      return {
        ...state,
        curSelected: state.curSelected - 1,
      };
    case AutocompleteActionKind.SET_CUR_SELECTED:
      return {
        ...state,
        curSelected: payload.curSelected,
      };
    // * Toggle autocomplete on/off
    case AutocompleteActionKind.SET_SHOW:
      return {
        ...state,
        show: payload.show,
      };
    // * Set current input being typed
    case AutocompleteActionKind.SET_CUR_INPUT:
      return {
        ...state,
        curInput: payload.curInput,
      };
    // * Set autocomplete full array
    case AutocompleteActionKind.SET_AUTO_ARR:
      return {
        ...state,
        autoArr: payload.autoArr,
      };
    default:
      return state;
  }
}
