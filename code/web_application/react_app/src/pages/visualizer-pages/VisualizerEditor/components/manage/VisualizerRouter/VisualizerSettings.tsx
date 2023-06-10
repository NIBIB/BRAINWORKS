import { DownloadIcon, SettingsIcon } from "@chakra-ui/icons";
import {
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
} from "@chakra-ui/react";
import { useAppSelector } from "../../../../../../store/hooks";
import { Tooltip } from "@chakra-ui/react";

const VisualizerSettings = () => {
  const curVisualizer = useAppSelector((state) => state.visualizer);

  const handleDownloadZip = () => {
    var a = document.createElement("a");
    a.href = "data:application/octet-stream;base64," + curVisualizer.zip_data;
    a.download = "BRAINWORKS.zip";
    a.click();
  };

  return (
    <Menu>
      <Tooltip hasArrow label="Settings" color="white">
        <MenuButton
          as={IconButton}
          aria-label="Options"
          icon={<SettingsIcon />}
          variant="ghost"
        />
      </Tooltip>
      <MenuList>
        <MenuItem icon={<DownloadIcon />} onClick={handleDownloadZip}>
          Download ZIP
        </MenuItem>
      </MenuList>
    </Menu>
  );
};

export default VisualizerSettings;
