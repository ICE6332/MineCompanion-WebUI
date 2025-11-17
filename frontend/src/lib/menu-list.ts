import { Monitor, Users, Settings, LayoutGrid } from "lucide-react";

type Submenu = {
  href: string;
  label: string;
  active?: boolean;
};

type Menu = {
  href: string;
  label: string;
  active?: boolean;
  icon: any;
  submenus?: Submenu[];
};

type Group = {
  groupLabel: string;
  menus: Menu[];
};

export function getMenuList(pathname: string): Group[] {
  return [
    {
      groupLabel: "",
      menus: [
        {
          href: "/",
          label: "控制台",
          icon: LayoutGrid,
          submenus: []
        }
      ]
    },
    {
      groupLabel: "角色管理",
      menus: [
        {
          href: "/test-card",
          label: "角色测试",
          icon: Users
        }
      ]
    },
    {
      groupLabel: "系统",
      menus: [
        {
          href: "/monitor",
          label: "监控面板",
          icon: Monitor
        },
        {
          href: "/settings",
          label: "系统设置",
          icon: Settings
        }
      ]
    }
  ];
}
