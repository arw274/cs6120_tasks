#include "llvm/Pass.h"
#include "llvm/IR/Module.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
using namespace llvm;

namespace {

struct MulToAddPass : public PassInfoMixin<MulToAddPass> {
    PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM) {
        bool changed = false;
        auto& ctx = M.getContext();
        auto* rettype = Type::getInt32Ty(ctx);
        std::vector<Type*> paramtypes = {Type::getInt32Ty(ctx), Type::getInt32Ty(ctx)};
        auto mua = M.getOrInsertFunction("mul_using_add", FunctionType::get(rettype, paramtypes, false));
        for (auto &F : M.functions()) {
            for (auto &B : F) {
                std::vector<Instruction*> to_erase;
                for (auto &I : B) {
                    if (auto *op = dyn_cast<BinaryOperator>(&I)) {
                        if (op->getOpcode() == llvm::Instruction::Mul){
                            Value* lhs = op->getOperand(0);
                            Value* rhs = op->getOperand(1);
                            if (lhs->getType()->isIntegerTy(32) && 
                                rhs->getType()->isIntegerTy(32) && 
                                op->getType()->isIntegerTy(32)) {

                                IRBuilder<> builder(op);
                                builder.SetInsertPoint(&B, ++builder.GetInsertPoint());
                                Value* args[] = {lhs, rhs};
                                Value* new_mul = builder.CreateCall(mua, args);
                                for (auto& U : op->uses()) {
                                    auto *user = U.getUser();
                                    user->setOperand(U.getOperandNo(), new_mul);
                                }
                                to_erase.push_back(op);
                            }
                        }
                    }
                }
                for (auto* op : to_erase)
                    op->eraseFromParent();
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
                    MPM.addPass(MulToAddPass());
                });
        }
    };
}
