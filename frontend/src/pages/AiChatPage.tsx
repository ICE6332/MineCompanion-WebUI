import { Link } from "react-router-dom";

import { ContentLayout } from "@/components/admin-panel/content-layout";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const AiChatPage = () => {
  return (
    <ContentLayout title="AI 对话">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/">主页</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>AI 对话</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="mt-6 space-y-6">
        <header className="space-y-2">
          <h2 className="text-3xl md:text-4xl font-bold">AI 对话</h2>
          <p className="text-muted-foreground max-w-3xl">
            这里将展示前端接入的 AI 对话功能，当前为占位页面，后续将补充交互组件。
          </p>
        </header>

        <section aria-labelledby="ai-chat-placeholder" className="max-w-4xl">
          <Card>
            <CardHeader>
              <CardTitle>功能建设中</CardTitle>
              <CardDescription>正在准备聊天界面与消息流，请稍后再来查看。</CardDescription>
            </CardHeader>
            <CardContent className="text-muted-foreground">
              页面骨架已就绪，可在此区域添加对话列表、输入框等组件。
            </CardContent>
          </Card>
        </section>
      </div>
    </ContentLayout>
  );
};

export default AiChatPage;
export { AiChatPage };
