"use client";

import { useState } from "react";
import { Plus, ArrowDown, Zap, Webhook, Database, Play, Settings, Bot, FileSearch, Sparkles, X } from "lucide-react";

type NodeType = "trigger" | "action";

interface Node {
  id: string;
  type: NodeType;
  title: string;
  icon: any;
  config: string;
}

const actionTypes = [
  { title: "RAG Document Retrieval", icon: FileSearch, config: "Query Vector Database (Pinecone)" },
  { title: "LLM Reasoning Engine", icon: Bot, config: "Analyze with GPT-4o" },
  { title: "Agentic Autonomous Decision", icon: Sparkles, config: "Determine next step" },
  { title: "Update Knowledge Graph", icon: Database, config: "Save findings to Neo4j" },
];

export default function AutomationPage() {
  const [nodes, setNodes] = useState<Node[]>([
    {
      id: "1",
      type: "trigger",
      title: "On New Webhook Event",
      icon: Webhook,
      config: "Listening on /api/webhook/agent",
    },
  ]);

  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const addAction = (action: typeof actionTypes[0]) => {
    setNodes([
      ...nodes,
      {
        id: Math.random().toString(36).substr(2, 9),
        type: "action",
        title: action.title,
        icon: action.icon,
        config: action.config,
      },
    ]);
    setIsMenuOpen(false);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-50 p-8">
      <div className="mx-auto max-w-4xl">
        <header className="mb-10 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 mb-3">
            Autonomous Agent Builder
          </h1>
          <p className="text-lg text-slate-500 max-w-2xl mx-auto">
            Visually chain your RAG pipelines and autonomous agent tasks. Take one trigger, perform an intelligent action, and keep connecting simply.
          </p>
        </header>

        <div className="flex flex-col items-center justify-start space-y-4 pb-32">
          {nodes.map((node, index) => (
            <div key={node.id} className="flex flex-col items-center relative w-full group">
              {/* Connection Line */}
              {index !== 0 && (
                <div className="h-10 w-0.5 bg-gradient-to-b from-indigo-300 to-blue-400 my-2 relative">
                  <ArrowDown className="absolute -bottom-3 -left-2 h-4 w-4 text-blue-500 animate-bounce" />
                </div>
              )}

              {/* Node Card */}
              <div 
                className={`w-full max-w-md rounded-2xl border bg-white p-5 shadow-lg shadow-slate-200/50 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 relative overflow-hidden ${
                  node.type === "trigger" ? "border-indigo-200 hover:shadow-indigo-100" : "border-slate-200 hover:shadow-blue-100"
                }`}
              >
                {/* Decorative background gradient */}
                <div className={`absolute top-0 left-0 w-1.5 h-full ${node.type === "trigger" ? "bg-gradient-to-b from-indigo-500 to-blue-500" : "bg-gradient-to-b from-blue-400 to-cyan-400"}`} />

                <div className="flex items-center justify-between ml-3">
                  <div className="flex items-center gap-4">
                    <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${
                      node.type === "trigger" ? "bg-indigo-50 text-indigo-600" : "bg-blue-50 text-blue-600"
                    }`}>
                      <node.icon className="h-6 w-6" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 text-lg">
                        {node.title}
                      </h3>
                      <p className="text-sm text-slate-500 flex items-center gap-1 mt-0.5">
                        <Settings className="h-3 w-3" />
                        {node.config}
                      </p>
                    </div>
                  </div>
                  {node.type === "trigger" && (
                    <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-700">
                      Trigger
                    </span>
                  )}
                  {node.type === "action" && (
                    <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
                      Action
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Add Action Button and Menu */}
          <div className="pt-8 w-full max-w-md flex flex-col items-center relative">
            {!isMenuOpen ? (
              <button
                onClick={() => setIsMenuOpen(true)}
                className="group relative inline-flex items-center justify-center gap-2 rounded-full bg-white px-8 py-3.5 text-sm font-semibold text-slate-700 shadow-sm border border-slate-200 hover:bg-slate-50 hover:border-slate-300 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 overflow-hidden"
              >
                <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-indigo-50/50 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
                <div className="bg-indigo-100 text-indigo-600 rounded-full p-1 -ml-2">
                  <Plus className="h-5 w-5 transition-transform group-hover:rotate-90" />
                </div>
                Add Next Action
              </button>
            ) : (
              <div className="w-full bg-white rounded-2xl border border-indigo-100 shadow-xl shadow-indigo-100/50 overflow-hidden animate-in fade-in slide-in-from-top-4 duration-200">
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50">
                  <span className="font-semibold text-slate-700 text-sm">Select an Action Node</span>
                  <button onClick={() => setIsMenuOpen(false)} className="text-slate-400 hover:text-slate-600">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <div className="flex flex-col p-2">
                  {actionTypes.map((action, idx) => (
                    <button
                      key={idx}
                      onClick={() => addAction(action)}
                      className="flex items-center gap-3 p-3 text-left rounded-xl hover:bg-indigo-50 transition-colors group"
                    >
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600 group-hover:bg-indigo-100 group-hover:text-indigo-600 transition-colors">
                        <action.icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-slate-800 text-sm group-hover:text-indigo-700 transition-colors">{action.title}</h4>
                        <p className="text-xs text-slate-500">{action.config}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Deploy / Activate Button */}
          <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40">
            <button className="flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-600 to-blue-600 px-10 py-4 text-base font-bold text-white shadow-xl shadow-indigo-500/40 hover:shadow-2xl hover:shadow-indigo-500/50 hover:-translate-y-1 transition-all">
              <Play className="h-5 w-5 fill-current" />
              Deploy RAG Pipeline
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
