import { Box } from "@chakra-ui/react";

interface AppProps {
  /**
   * `string[]` -
   */
  searchQuery: string[];
  curSelected: number;
  setCurSelected: (val: number) => void;
  show: boolean;
  addFormValue: (value: string) => void;
}

/**
 * FormikAutoComplete
 *
 * If a valid autocomplete file string is given, pulls that autocomplete file and allows user to select from list
 */
const FormikAutoComplete = ({
  searchQuery,
  curSelected,
  show,
  setCurSelected,
  addFormValue,
}: AppProps) => {
  return (
    <>
      {show && (
        <Box
          id="tries"
          border="1px"
          borderRadius="sm"
          borderColor="gray.300"
          w="100%"
          pos="absolute"
          top="105%"
          bg="white"
          zIndex={1000}
          tabIndex={0}
          boxShadow="md"
        >
          {/* Autocomplete list items */}
          {searchQuery?.length > 0 ? (
            searchQuery.map((result, index) => {
              return (
                <Box
                  w="100%"
                  textAlign={"left"}
                  p="10px"
                  bg={curSelected === index ? "gray.100" : "white"}
                  key={result[0]}
                  onMouseOver={() => {
                    setCurSelected(index);
                  }}
                  onClick={() => {
                    addFormValue(searchQuery[curSelected][0]);
                  }}
                >
                  {result[0]}
                  <Box as={"span"} color={"gray.600"} ml={"3"}>
                    {result[1].toLocaleString()} results
                  </Box>
                </Box>
              );
            })
          ) : (
            <Box w="100%" textAlign={"left"} p="10px" bg={"white"}>
              <Box as={"span"} color={"gray.600"} ml={"3"}>
                Your search did not yield any results
              </Box>
            </Box>
          )}
        </Box>
      )}
    </>
  );
};

export default FormikAutoComplete;
