import { Text, Tooltip } from "@chakra-ui/react";
import { brand100 } from "../../../../../../setup/theme/colors";

interface AppProps {
  def?: string;
  text: string;
}

const TableFragment = ({ def, text }: AppProps) => {
  return (
    <Tooltip hasArrow label={def} color="white" isDisabled={!def}>
      <Text as="span" bg={def ? brand100 : ""} ml={1}>
        {text}
      </Text>
    </Tooltip>
  );
};

export default TableFragment;
