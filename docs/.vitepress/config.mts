import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Cost Cutter",
  description: "A kill-switch for AWS",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "Home", link: "/" },
      { text: "Guide", link: "/guide/what-is-costcutter" },
    ],

    sidebar: [
      {
        text: "Introduction",
        items: [
          { text: "What is CostCutter?", link: "/guide/what-is-costcutter" },
          { text: "Getting Started (CLI)", link: "/guide/getting-started" },
          {
            text: "Getting Started (Terraform)",
            link: "/guide/getting-started-terraform",
          },
        ],
      },
      {
        text: "Usage",
        items: [
          { text: "Usage (CLI)", link: "/usage-cli" },
          { text: "Usage (Terraform)", link: "/usage-terraform" },
        ],
      },
      {
        text: "Reference",
        items: [
          { text: "Config Reference", link: "/guide/config-reference" },
          //   {
          //     text: "Supported Services & Resources",
          //     link: "/guide/supported-services",
          //   },
        ],
      },
      //   {
      //     text: "Guide",
      //     items: [
      //       { text: "How It Works", link: "/guide/how-it-works" },
      //       { text: "Architecture", link: "/guide/architecture" },
      //       { text: "Troubleshooting & FAQ", link: "/guide/troubleshooting" },
      //     ],
      //   },
      //   {
      //     text: "Contributing",
      //     items: [{ text: "How to Contribute", link: "/guide/contributing" }],
      //   },
    ],

    socialLinks: [
      { icon: "github", link: "https://github.com/HYP3R00T/costcutter" },
    ],
  },
});
