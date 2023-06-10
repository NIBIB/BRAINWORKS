const Divider = {
  variants: {
    thick: {
      height: "10px",
      background: "brand",
      opacity: "100%",
    },
    bold: {
      height: "1px",
      background: "purple.100",
      opacity: "100%",
    },
  },
};

const Input = {
  baseStyle: {
    borderColor: "black",
  },
};

const ModalHeader = {
  baseStyle: {
    fontSize: "40px",
  },
};

const Heading = {
  variants: {
    "call-to-action": {
      fontWeight: "700",
      fontSize: "8xl",
      color: "brandAlt",
      lineHeight: "100%",
    },
  },
};

const components = {
  Heading,
  // Button,
  Divider,
  Text,
  Input,
  ModalHeader,
};

export default components;
