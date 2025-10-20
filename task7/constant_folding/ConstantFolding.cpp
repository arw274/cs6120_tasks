#include "llvm/Pass.h"
#include "llvm/IR/Module.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
using namespace llvm;

namespace {

struct ConstantFoldingPass : public PassInfoMixin<ConstantFoldingPass> {
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM) {
        bool changed = false;
        for (auto &F : M.functions()) {
            for (auto &B : F) {
                for (auto &I : B) {
                    if (auto *op = dyn_cast<BinaryOperator>(&I)) {
                        if (Constant *lhs = dyn_cast<Constant>(op->getOperand(0))) {
                            if (Constant *rhs = dyn_cast<Constant>(op->getOperand(1))) {
                                Constant *result = ConstantExpr::get(op->getOpcode(), lhs, rhs);
                                
                                // Everywhere the old instruction was used as an operand, use our
                                // new computed value instead.
                                for (auto& U : op->uses()) {
                                    User* user = U.getUser();  // A User is anything with operands.
                                    user->setOperand(U.getOperandNo(), result);
                                    errs() << "Folded constant expression" << *op << " to " << *result << "\n";
                                }
                                op->eraseFromParent();
                                changed = true;
                            }
                        }
                    }
                }
            }
        }
        if (changed) {
            return PreservedAnalyses::none();
        }
        return PreservedAnalyses::all();
    };
};

}

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
    return {
        .APIVersion = LLVM_PLUGIN_API_VERSION,
        .PluginName = "Constant Folding Pass",
        .PluginVersion = "v0.1",
        .RegisterPassBuilderCallbacks = [](PassBuilder &PB) {
            PB.registerPipelineStartEPCallback(
                [](ModulePassManager &MPM, OptimizationLevel Level) {
                    MPM.addPass(ConstantFoldingPass());
                });
        }
    };
}
