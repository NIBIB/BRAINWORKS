import {
  HStack,
  StackProps,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
} from "@chakra-ui/react";
import { ReactNode } from "react";

import { brandColorScheme } from "../../../setup/theme/colors";

type MenuItemType = { name: string; component: ReactNode };

interface AppProps {
  items: MenuItemType[];
  tabListStyleProps?: StackProps;
}

/**
 * MenuTab
 *
 * React component that renders ChakraUI tab panels given array
 */
const MenuTab = ({ items, tabListStyleProps }: AppProps) => {
  return (
    <Tabs isLazy variant="soft-rounded" colorScheme={brandColorScheme}>
      <HStack {...tabListStyleProps}>
        <TabList>
          {items.map((item) => (
            <Tab key={item.name}>{item.name}</Tab>
          ))}
        </TabList>
      </HStack>
      <TabPanels>
        {items.map((item) => (
          <TabPanel key={item.name}>{item.component}</TabPanel>
        ))}
      </TabPanels>
    </Tabs>
  );
};

export default MenuTab;
