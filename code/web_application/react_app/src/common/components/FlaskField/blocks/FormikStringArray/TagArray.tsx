import { Tag, TagCloseButton, TagLabel, Wrap } from "@chakra-ui/react";
import { brandColorScheme } from "../../../../../setup/theme/colors";

interface AppProps {
  /**
   * array - `string array` String array holding all tag labels
   */
  array: string[];
  /**
   * property - `string` Property key of value object
   */
  property: string;
  /**
   * On close - `function` Function that runs when tag close is clicked, removes tag from list
   */
  onClose: any;
}

/**
 * TagArray
 *
 * React component that maps array of strings to Chakra UI tags with the ability to remove the tags
 */
const TagArray = ({ array, onClose, property }: AppProps) => {
  return (
    <Wrap>
      {array?.map((value: string, index: number) => (
        <Tag
          size={"sm"}
          key={index}
          variant="subtle"
          colorScheme={brandColorScheme}
        >
          <TagLabel>{value}</TagLabel>
          <TagCloseButton
            onClick={() => {
              const filtered = array.filter((item: string) => item !== value);
              onClose(property, filtered);
            }}
          />
        </Tag>
      ))}
    </Wrap>
  );
};

export default TagArray;
