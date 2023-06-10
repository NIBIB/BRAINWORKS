import {
  Box,
  Button,
  Input,
  InputGroup,
  InputRightElement,
} from "@chakra-ui/react";
import useAxios from "axios-hooks";
import { useFormikContext } from "formik";
import {
  ChangeEvent,
  FocusEvent,
  KeyboardEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import useGlobalFormik from "../../../../hooks/useGlobalFormik";
import useGlobalAlert from "../../../../hooks/useGlobalAlert";
import TagArray from "./TagArray";
import FormikAutoComplete from "./FormikAutoComplete";
import { API_URL } from "../../../../templates/api";
import { getFieldInfo, matchItems } from "../../../../utils";
import { FiPlus } from "react-icons/fi";

interface AppProps {
  /**
   * `string` is the name of the property
   */
  property: string;
}
/**
 *
 * FormikStringArray
 *
 * React component that renders an input field that adds to a string array on submit/return
 */
const FormikStringArray = ({ property }: AppProps) => {
  const { formikSlice } = useGlobalFormik();
  const { values, setFieldValue } = useFormikContext<any>();
  const { showGlobalAlert } = useGlobalAlert();
  const inputRef = useRef<HTMLInputElement | null>(null);

  // * State tracks current input in form field, on `enter` key the field clears and is added to the Formik values
  const [curInput, setCurInput] = useState("");

  // * Tracks autocomplete full data
  const [autoArr, setAutoArr] = useState<string[]>([]);

  // * Tracks current selected autocomplete item
  const [curSelected, setCurSelected] = useState(0);

  // * Enables / disables autocomplete popup based on clicking off the popup/pressing esc
  const [show, setShow] = useState(false);

  // * Returns all field info, give property
  const field = getFieldInfo(formikSlice.fieldsInfo, property);

  // * Add input to form value
  const addFormValue = (value: string) => {
    // * Don't add empty value
    if (value.length === 0) {
      showGlobalAlert("Error!", "Please write a term to add", "error", 3000);
      return;
    }
    // * Not add duplicate
    if (values[property]?.includes(value)) {
      showGlobalAlert(
        "Error!",
        "Please do not add duplicate values",
        "error",
        3000
      );
      return;
    }
    const valuesArr = values[property];
    if (valuesArr) {
      setFieldValue(property, [...valuesArr, value]);
    } else {
      setFieldValue(property, [value]);
    }
    // * Set current input to empty string
    setCurInput("");
  };

  // * Fetch autocomplete files
  const [, getAutocomplete] = useAxios<any>(
    {
      url: `${API_URL}/autocomplete/${field?.autocomplete}`,
      withCredentials: true,
    },
    { manual: true }
  );

  // * Fetch autocomplete files if autocomplete file is given
  useEffect(() => {
    const loadAutocomplete = async () => {
      const { data } = await getAutocomplete();
      setAutoArr(data);
    };
    if (field?.autocomplete) {
      loadAutocomplete();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [field?.autocomplete]);

  // * Rerenders autocomplete query if input
  const searchQuery = useMemo<string[]>(() => {
    if (field?.autocomplete && show) {
      if (curInput.length > 0) {
        return matchItems(curInput, autoArr);
      }
      return matchItems("a", autoArr);
    }
  }, [field?.autocomplete, curInput, autoArr, show]);

  return (
    <Box w="100%">
      {values[property]?.length > 0 && (
        <Box mb={3}>
          <TagArray
            array={values[property]}
            property={property}
            onClose={setFieldValue}
          />
        </Box>
      )}
      <InputGroup>
        <Input
          ref={inputRef}
          type="input"
          id={property}
          value={curInput}
          autoComplete="off"
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            setCurInput(e.currentTarget.value);
          }}
          name={property}
          onBlur={(_event: FocusEvent<HTMLInputElement>) => {
            // * When focusing the input initially, setShow to false, hide autocorrect
            setTimeout(() => {
              setShow(false);
            }, 100);
          }}
          onFocus={(_event: FocusEvent<HTMLInputElement>) => {
            // * When focusing the input initially, setShow to true, hide autocorrect
            setShow(true);
          }}
          onKeyDown={(event: KeyboardEvent<HTMLInputElement>) => {
            const { key } = event;
            // * Autocomplete field is currently enabled
            if (show && searchQuery?.length > 0) {
              const newValue = searchQuery[curSelected][0];
              if (key === "ArrowDown") {
                // * Move current selected up and down (min 0, max 4)
                if (curSelected < 4) {
                  setCurSelected((prevState) => prevState + 1);
                } else {
                  setCurSelected(0);
                }
              }
              if (key === "ArrowUp") {
                if (curSelected > 0) {
                  setCurSelected((prevState) => prevState - 1);
                } else {
                  setCurSelected(4);
                }
              }
              // * Submit currently selected search query
              if (key === "Enter" || key === "Tab") {
                addFormValue(newValue);
              }
            } else {
              //* On "enter key", add value to string array if it does not exist already
              if (key === "Enter" || key === "Tab") {
                // * Reject if added value is not in search query & autocomplete field is enabled
                if (field?.autocomplete.length > 0) {
                  showGlobalAlert(
                    "Warning!",
                    "Please submit a value from the autocomplete dropdown",
                    "warning",
                    3000
                  );
                  return;
                }
                addFormValue(curInput);
              }
            }
          }}
        />

        {/* <InputRightElement width="6.5rem">
          <Button
            variant="outline"
            h="1.75rem"
            size="xs"
            leftIcon={<FiPlus />}
            onClick={() => {
              if (field?.autocomplete) {
                // * Autocomplete enabled, make the button show autocomplete on first press
                if (inputRef) {
                  console.log("focus");
                  inputRef.current?.focus();
                }
              } else {
                // * Autocomplete not enable, just add current input
                addFormValue(curInput);
              }
            }}
          >
            Add term
          </Button>
        </InputRightElement> */}
      </InputGroup>
      {/* Autocomplete list if exists */}
      {field?.autocomplete.length > 0 && (
        <FormikAutoComplete
          searchQuery={searchQuery}
          curSelected={curSelected}
          setCurSelected={setCurSelected}
          show={show}
          addFormValue={addFormValue}
        />
      )}
    </Box>
  );
};
export default FormikStringArray;
