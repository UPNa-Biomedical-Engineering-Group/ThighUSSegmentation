import os
import sys
import sysconfig
import traceback
import importlib
import importlib.metadata
import importlib.util
import subprocess
import contextlib
from pathlib import Path

import slicer
from slicer.ScriptedLoadableModule import *
from qt import QIcon
import ctk

from qt import (
    QPushButton,
    QLineEdit,
    QLabel,
    QFormLayout,
    QWidget,
    QCheckBox,
    QPlainTextEdit,
)


class ThighUSSegmentation(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        iconPath = os.path.join(
            os.path.dirname(__file__),
            "Resources",
            "Icons",
            "ThighUSSegmentation.png",
        )

        parent.icon = QIcon(iconPath)

        self.parent.title = "Thigh US Segmentation"
        self.parent.categories = ["Segmentation"]
        self.parent.dependencies = []
        self.parent.contributors = [
            "Mara Concepción Alvarez",
            "Paula Crespo Ortega",
            "Arantxa Villanueva Larre",
            "Rafael Cabeza Laguna",
        ]
        self.parent.helpText = (
            "Automatic thigh ultrasound segmentation using nnU-Net."
        )
        self.parent.acknowledgementText = ""


class ThighUSSegmentationWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        self.logic = ThighUSSegmentationLogic()
        self.logic.setLogCallback(self.appendLog)

        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.inputSelector.selectNodeUponCreation = True
        self.inputSelector.addEnabled = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.noneEnabled = False
        self.inputSelector.setMRMLScene(slicer.mrmlScene)

        self.caseIdEdit = QLineEdit()
        self.caseIdEdit.setText("")

        self.caseIdManuallyEdited = False
        self.updatingCaseIdFromCode = False

        self.caseIdEdit.textChanged.connect(self.onCaseIdEdited)
        self.inputSelector.currentNodeChanged.connect(self.onInputNodeChanged)

        self.outputDirEdit = ctk.ctkPathLineEdit()
        self.outputDirEdit.filters = ctk.ctkPathLineEdit.Dirs

        self.loadLabelmapCheckBox = QCheckBox("Load labelmap")
        self.loadLabelmapCheckBox.setChecked(True)

        self.loadSegmentationCheckBox = QCheckBox("Load segmentation")
        self.loadSegmentationCheckBox.setChecked(True)

        self.loadMarkupsCheckBox = QCheckBox(
            "Load anatomical points and central line"
        )
        self.loadMarkupsCheckBox.setChecked(True)

        self.loadTableCheckBox = QCheckBox("Load results table")
        self.loadTableCheckBox.setChecked(True)

        self.applyButton = QPushButton("Apply")
        self.applyButton.clicked.connect(self.onApply)

        self.statusLabel = QLabel("Ready.")

        self.logBox = QPlainTextEdit()
        self.logBox.setReadOnly(True)
        self.logBox.setMinimumHeight(260)
        self.logBox.appendPlainText("Ready.")

        formLayout = QFormLayout()

        inputHelpLabel = QLabel("Load an input image.")
        inputHelpLabel.setWordWrap(True)
        inputHelpLabel.setStyleSheet("font-style: italic;")

        caseIdHelpLabel = QLabel(
            "Enter the identifier you want to use for this case. "
            "By default, it is taken from the input image name."
        )
        caseIdHelpLabel.setWordWrap(True)
        caseIdHelpLabel.setStyleSheet("font-style: italic;")

        outputHelpLabel = QLabel(
            "Select the folder where the output files will be saved."
        )
        outputHelpLabel.setWordWrap(True)
        outputHelpLabel.setStyleSheet("font-style: italic;")

        formLayout.addRow(inputHelpLabel)
        formLayout.addRow("Input image:", self.inputSelector)

        formLayout.addRow(caseIdHelpLabel)
        formLayout.addRow("Case ID:", self.caseIdEdit)

        formLayout.addRow(outputHelpLabel)
        formLayout.addRow("Output folder:", self.outputDirEdit)

        formLayout.addRow("Outputs:", self.loadLabelmapCheckBox)
        formLayout.addRow("", self.loadSegmentationCheckBox)
        formLayout.addRow("", self.loadMarkupsCheckBox)
        formLayout.addRow("", self.loadTableCheckBox)
        formLayout.addRow(self.applyButton)
        formLayout.addRow("Status:", self.statusLabel)
        formLayout.addRow("Progress log:", self.logBox)

        widget = QWidget()
        widget.setLayout(formLayout)

        self.layout.addWidget(widget)
        self.layout.addStretch(1)

        self.updateCaseIdFromInputNode(force=True)

    def sanitizeCaseId(self, text):
        text = str(text).strip()

        invalidChars = [" ", "/", "\\", ":", "*", "?", '"', "<", ">", "|"]

        for char in invalidChars:
            text = text.replace(char, "_")

        while "__" in text:
            text = text.replace("__", "_")

        text = text.strip("_")

        if not text:
            text = "case001"

        return text

    def setCaseIdFromCode(self, text):
        self.updatingCaseIdFromCode = True

        self.caseIdEdit.blockSignals(True)
        self.caseIdEdit.setText(text)
        self.caseIdEdit.blockSignals(False)

        self.updatingCaseIdFromCode = False

    def onCaseIdEdited(self, *args):
        if self.updatingCaseIdFromCode:
            return

        self.caseIdManuallyEdited = True

    def updateCaseIdFromInputNode(self, force=False):
        node = self.inputSelector.currentNode()

        if node is None:
            return

        currentCaseId = self.caseIdEdit.text.strip()

        if not force:
            if self.caseIdManuallyEdited and currentCaseId:
                return

        suggestedCaseId = self.sanitizeCaseId(node.GetName())

        self.setCaseIdFromCode(suggestedCaseId)
        self.caseIdManuallyEdited = False

    def onInputNodeChanged(self, node):
        """
        Cada vez que el usuario selecciona una nueva imagen,
        el Case ID se actualiza automáticamente con el nombre de esa imagen.

        Si después el usuario quiere modificarlo manualmente, puede hacerlo.
        Pero al seleccionar otra imagen nueva, se vuelve a usar el nombre
        de la nueva imagen como Case ID.
        """
        if node is None:
            return

        suggestedCaseId = self.sanitizeCaseId(node.GetName())

        self.setCaseIdFromCode(suggestedCaseId)
        self.caseIdManuallyEdited = False

    def appendLog(self, text):
        if text is None:
            return

        text = str(text)

        if text.strip() == "":
            return

        self.logBox.appendPlainText(text.rstrip())
        self.logBox.verticalScrollBar().setValue(
            self.logBox.verticalScrollBar().maximum
        )
        slicer.app.processEvents()

    def onApply(self):
        inputNode = self.inputSelector.currentNode()

        if inputNode is None:
            slicer.util.errorDisplay("Select an input image.")
            return

        caseId = self.sanitizeCaseId(self.caseIdEdit.text)
        self.caseIdEdit.setText(caseId)

        outputRoot = self.outputDirEdit.currentPath

        if not caseId:
            slicer.util.errorDisplay("Case ID cannot be empty.")
            return

        if not outputRoot:
            slicer.util.errorDisplay("Select an output folder.")
            return

        self.logBox.clear()
        self.appendLog("=== Thigh US Segmentation ===")
        self.appendLog(f"Case ID: {caseId}")
        self.appendLog(f"Output folder: {outputRoot}")

        self.statusLabel.text = "Running..."
        self.applyButton.setEnabled(False)
        slicer.app.processEvents()

        try:
            result, loadedNodes = self.logic.run(
                inputNode=inputNode,
                outputRoot=outputRoot,
                caseId=caseId,
                loadLabelmap=self.loadLabelmapCheckBox.checked,
                loadSegmentation=self.loadSegmentationCheckBox.checked,
                loadMarkups=self.loadMarkupsCheckBox.checked,
                loadTable=self.loadTableCheckBox.checked,
            )

            dfResults = result.get("df_results")
            distancesWereCalculated = (
                dfResults is not None and not dfResults.empty
            )

            self.statusLabel.text = "Done."
            self.appendLog("")
            self.appendLog("=== Pipeline completed successfully ===")

            for key in loadedNodes.keys():
                self.appendLog(f"Loaded: {key}")

            if distancesWereCalculated:
                slicer.util.infoDisplay(
                    "Pipeline completed successfully.\n\n"
                    f"Case ID: {caseId}\n"
                    f"Output folder:\n{result['case_dir']}"
                )
            else:
                slicer.util.warningDisplay(
                    "The femur was not detected.\n\n"
                    "Thickness measurements could not be calculated because "
                    "the femur segmentation is missing.\n\n"
                    "Only the available segmentations have been loaded. "
                    "Anatomical points and the central line were not loaded."
                )

        except Exception:
            self.statusLabel.text = "Error."

            errorText = traceback.format_exc()
            self.appendLog("")
            self.appendLog("=== ERROR ===")
            self.appendLog(errorText)

            slicer.util.errorDisplay(
                "An error occurred during ThighUSSegmentation.\n\n"
                "See the progress log for details."
            )

        finally:
            self.applyButton.setEnabled(True)
            slicer.app.processEvents()


class SlicerLogWriter:
    """
    Redirige stdout/stderr al cuadro de log del módulo.
    """

    def __init__(self, logCallback):
        self.logCallback = logCallback
        self.buffer = ""

    def write(self, text):
        if not text:
            return

        self.buffer += text

        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self.logCallback(line)

    def flush(self):
        if self.buffer.strip():
            self.logCallback(self.buffer)
            self.buffer = ""


class ThighUSSegmentationLogic(ScriptedLoadableModuleLogic):

    PACKAGE_MIN_VERSION = "0.2.5"
    PACKAGE_SPEC = f"thigh-us-segmentation>={PACKAGE_MIN_VERSION}"
    PACKAGE_DISTRIBUTION_NAME = "thigh-us-segmentation"
    PACKAGE_IMPORT_NAME = "ThighUSSegmentation"

    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)
        self.logCallback = None

    def setLogCallback(self, callback):
        self.logCallback = callback

    def log(self, text):
        if self.logCallback:
            self.logCallback(text)
        else:
            print(text)

    def package_distribution_installed(self):
        """
        Comprueba si está instalada la distribución pip real:
        thigh-us-segmentation.

        No usamos importlib.util.find_spec("ThighUSSegmentation") porque
        el módulo de Slicer también se llama ThighUSSegmentation.py.
        """
        try:
            importlib.metadata.version(self.PACKAGE_DISTRIBUTION_NAME)
            return True
        except importlib.metadata.PackageNotFoundError:
            return False

    def get_package_version(self):
        try:
            return importlib.metadata.version(
                self.PACKAGE_DISTRIBUTION_NAME
            )
        except importlib.metadata.PackageNotFoundError:
            return None

    def package_version_is_compatible(self):
        """
        Check whether the installed thigh-us-segmentation version
        satisfies the minimum version required by this extension.
        """
        version = self.get_package_version()

        if version is None:
            return False

        from packaging.version import Version

        return Version(version) >= Version(self.PACKAGE_MIN_VERSION)

    def get_run_full_pipeline(self):
        """
        Importa run_full_pipeline desde la librería instalada por pip,
        evitando el conflicto con este módulo de Slicer, que también se llama
        ThighUSSegmentation.py.
        """

        try:
            dist = importlib.metadata.distribution(
                self.PACKAGE_DISTRIBUTION_NAME
            )
        except importlib.metadata.PackageNotFoundError as e:
            raise RuntimeError(
                "La librería thigh-us-segmentation no está instalada."
            ) from e

        initPath = Path(
            dist.locate_file(f"{self.PACKAGE_IMPORT_NAME}/__init__.py")
        )

        if not initPath.exists():
            raise RuntimeError(
                "No se encontró el paquete instalado ThighUSSegmentation "
                "en site-packages.\n"
                f"Ruta esperada: {initPath}"
            )

        aliasName = "_ThighUSSegmentationLibrary"

        if aliasName in sys.modules:
            module = sys.modules[aliasName]
            return module.run_full_pipeline

        spec = importlib.util.spec_from_file_location(
            aliasName,
            str(initPath),
            submodule_search_locations=[str(initPath.parent)],
        )

        if spec is None or spec.loader is None:
            raise RuntimeError(
                f"No se pudo crear el import spec para: {initPath}"
            )

        module = importlib.util.module_from_spec(spec)
        sys.modules[aliasName] = module
        spec.loader.exec_module(module)

        if not hasattr(module, "run_full_pipeline"):
            raise RuntimeError(
                "El paquete instalado no expone run_full_pipeline."
            )

        return module.run_full_pipeline

    def add_slicer_python_scripts_to_path(self):
        """
        Asegura que los ejecutables instalados por pip dentro de Slicer
        estén disponibles, especialmente:

        nnUNetv2_predict_from_modelfolder
        """

        possibleDirs = []

        exePath = Path(sys.executable).resolve()
        exeDir = exePath.parent

        possibleDirs.append(exeDir)
        possibleDirs.append(exeDir / "Scripts")
        possibleDirs.append(exeDir.parent / "Scripts")
        possibleDirs.append(exeDir.parent / "bin")
        possibleDirs.append(exeDir.parent / "lib" / "Python" / "Scripts")

        scriptsPath = sysconfig.get_path("scripts")
        if scriptsPath:
            possibleDirs.append(Path(scriptsPath))

        existingDirs = []
        for path in possibleDirs:
            try:
                path = Path(path).resolve()
                if path.exists() and str(path) not in existingDirs:
                    existingDirs.append(str(path))
            except Exception:
                pass

        currentPath = os.environ.get("PATH", "")
        pathParts = currentPath.split(os.pathsep) if currentPath else []

        for scriptsDir in existingDirs:
            if scriptsDir not in pathParts:
                pathParts.insert(0, scriptsDir)

        os.environ["PATH"] = os.pathsep.join(pathParts)

        self.log("PATH actualizado para buscar ejecutables de nnU-Net.")
        for scriptsDir in existingDirs:
            self.log(f"Scripts dir: {scriptsDir}")

    def run_process_and_log(self, cmd):
        """
        Ejecuta un proceso externo y muestra stdout/stderr en el log.
        Se usa para pip install.
        """

        self.log("")
        self.log("Running command:")
        self.log(" ".join(str(c) for c in cmd))
        self.log("")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            universal_newlines=True,
        )

        if process.stdout is not None:
            for line in process.stdout:
                self.log(line.rstrip())

        returnCode = process.wait()

        if returnCode != 0:
            raise RuntimeError(
                "Command failed with return code "
                f"{returnCode}:\n{' '.join(str(c) for c in cmd)}"
            )

    def install_dependencies_if_needed(self):
        """
        Ensure that a compatible version of thigh-us-segmentation
        is installed in Slicer's Python environment.

        If the package is not installed, it is installed automatically.
        If an older incompatible version is installed, it is upgraded.
        """

        self.log("")
        self.log("=== Checking dependencies ===")
        self.log(f"Slicer Python executable: {sys.executable}")
        self.log(f"Slicer Python version: {sys.version}")

        # Check Python version
        if sys.version_info < (3, 10):
            raise RuntimeError(
                "ThighUSSegmentation requires Python >= 3.10.\n"
                f"This Slicer Python is: {sys.version}"
            )

        # Check whether thigh-us-segmentation is already installed
        packageInstalled = self.package_distribution_installed()

        if packageInstalled:
            version = self.get_package_version()

            if self.package_version_is_compatible():
                self.log(
                    f"{self.PACKAGE_DISTRIBUTION_NAME} is already installed. "
                    f"Version: {version}"
                )
                self.log(
                    f"Version requirement satisfied: "
                    f">= {self.PACKAGE_MIN_VERSION}"
                )

                self.add_slicer_python_scripts_to_path()
                return

            self.log(
                f"{self.PACKAGE_DISTRIBUTION_NAME} version {version} "
                f"is installed, but version >= "
                f"{self.PACKAGE_MIN_VERSION} is required."
            )
            self.log("Upgrading package and dependencies...")

        else:
            self.log(
                f"{self.PACKAGE_DISTRIBUTION_NAME} is not installed."
            )
            self.log(
                "Installing package and dependencies inside Slicer Python..."
            )

        self.log("This can take several minutes on first use.")

        # Upgrade pip
        self.run_process_and_log([
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
        ])

        # Install or upgrade thigh-us-segmentation
        self.run_process_and_log([
            sys.executable,
            "-m",
            "pip",
            "install",
            self.PACKAGE_SPEC,
        ])

        importlib.invalidate_caches()

        # Make pip-installed command-line tools available
        self.add_slicer_python_scripts_to_path()

        # Validate that the package is installed
        if not self.package_distribution_installed():
            raise RuntimeError(
                "thigh-us-segmentation could not be found after "
                "installation.\n"
                "Restart Slicer and try again."
            )

        version = self.get_package_version()

        # Validate the installed version
        if not self.package_version_is_compatible():
            raise RuntimeError(
                "A compatible version of thigh-us-segmentation could not be "
                "installed.\n"
                f"Installed version: {version}\n"
                f"Required version: >= {self.PACKAGE_MIN_VERSION}"
            )

        self.log(
            f"Dependencies installed successfully. Version: {version}"
        )

    def sort_markups_loading_order(self, mrkPaths):
        """
        Ordena los markups para que Slicer cargue primero la línea central
        y después los puntos anatómicos.

        Orden:
        1. central_line
        2. epidermis
        3. fascia_lata
        4. aponeurosis
        5. femur
        6. otros
        """

        priority = {
            "central_line": 0,
            "epidermis": 1,
            "fascia_lata": 2,
            "aponeurosis": 3,
            "femur": 4,
        }

        def get_priority(item):
            markupName, markupPath = item

            nameLower = str(markupName).lower()
            pathLower = str(markupPath).lower()

            for key, value in priority.items():
                if key in nameLower or key in pathLower:
                    return value

            return 99

        return sorted(
            mrkPaths.items(),
            key=get_priority,
        )

    def run(
        self,
        inputNode,
        outputRoot,
        caseId,
        loadLabelmap=True,
        loadSegmentation=True,
        loadMarkups=True,
        loadTable=True,
    ):
        self.install_dependencies_if_needed()

        self.log("")
        self.log("=== Importing ThighUSSegmentation library ===")

        run_full_pipeline = self.get_run_full_pipeline()

        outputRoot = Path(outputRoot)
        caseDir = outputRoot / caseId
        caseDir.mkdir(parents=True, exist_ok=True)

        inputMhaPath = caseDir / f"{caseId}_slicer_input.mha"

        if inputMhaPath.exists():
            inputMhaPath.unlink()

        self.log("")
        self.log("=== Saving input image ===")
        self.log(f"Input MHA: {inputMhaPath}")

        slicer.util.saveNode(inputNode, str(inputMhaPath))

        self.log("")
        self.log("=== Running full pipeline ===")
        self.log("If model weights are missing, they will be downloaded now.")
        self.log("The following messages come from the Python library:")
        self.log("")

        logWriter = SlicerLogWriter(self.log)

        with contextlib.redirect_stdout(
            logWriter
        ), contextlib.redirect_stderr(logWriter):
            result = run_full_pipeline(
                input_image_path=str(inputMhaPath),
                output_root=str(outputRoot),
                case_id=caseId,
                create_seg_nrrd=True,
            )

        logWriter.flush()

        dfResults = result.get("df_results")
        distancesWereCalculated = (
            dfResults is not None and not dfResults.empty
        )

        if not distancesWereCalculated:
            self.log("")
            self.log("WARNING: The femur was not detected.")
            self.log("Thickness measurements could not be calculated.")
            self.log("Anatomical points and central line will not be loaded.")
            self.log("Results table will not be loaded.")

        self.log("")
        self.log("=== Saving results table ===")

        csvPath = caseDir / f"{caseId}_results.csv"

        if distancesWereCalculated:
            result["df_results"].to_csv(csvPath, index=False)
            self.log(f"Results CSV: {csvPath}")
        else:
            csvPath = None
            self.log(
                "Results table was not saved because thickness measurements "
                "were not calculated."
            )

        loadedNodes = {}

        if loadLabelmap:
            self.log("")
            self.log("=== Loading labelmap ===")

            labelmapPath = result.get("labelmap_path")

            if labelmapPath and Path(labelmapPath).exists():
                labelmapNode = slicer.util.loadLabelVolume(str(labelmapPath))
                labelmapNode.SetName(f"{caseId}_labelmap")
                loadedNodes["labelmap"] = labelmapNode
                self.log(f"Loaded labelmap: {labelmapPath}")
            else:
                self.log("Labelmap not found.")

        if loadSegmentation:
            self.log("")
            self.log("=== Loading segmentation ===")

            segNrrdPath = result.get("seg_nrrd_path")

            if segNrrdPath and Path(segNrrdPath).exists():
                try:
                    segmentationNode = slicer.util.loadSegmentation(
                        str(segNrrdPath)
                    )
                except AttributeError:
                    segmentationNode = slicer.util.loadNodeFromFile(
                        str(segNrrdPath),
                        "SegmentationFile",
                    )

                segmentationNode.SetName(f"{caseId}_segmentation")
                loadedNodes["segmentation"] = segmentationNode
                self.log(f"Loaded segmentation: {segNrrdPath}")
            else:
                self.log("Segmentation .seg.nrrd not found.")

        if loadMarkups and distancesWereCalculated:
            self.log("")
            self.log("=== Loading anatomical markups ===")

            mrkPaths = result.get("mrk_paths", {})

            if not mrkPaths:
                self.log("No markups found in result.")
            else:
                orderedMrkPaths = self.sort_markups_loading_order(mrkPaths)

                self.log("Markup loading order:")
                for markupName, markupPath in orderedMrkPaths:
                    self.log(f"- {markupName}: {markupPath}")

                for markupName, markupPath in orderedMrkPaths:
                    markupPath = Path(markupPath)

                    if markupPath.exists():
                        markupNode = slicer.util.loadMarkups(str(markupPath))
                        markupNode.SetName(f"{caseId}_{markupName}")
                        loadedNodes[f"markup_{markupName}"] = markupNode
                        self.log(
                            f"Loaded markup {markupName}: {markupPath}"
                        )
                    else:
                        self.log(f"Markup not found: {markupPath}")

        elif loadMarkups and not distancesWereCalculated:
            self.log("")
            self.log("=== Loading anatomical markups ===")
            self.log("Skipped because the femur was not detected.")

        if loadTable and distancesWereCalculated:
            self.log("")
            self.log("=== Loading results table ===")

            if csvPath is not None and csvPath.exists():
                tableNode = slicer.util.loadTable(str(csvPath))
                tableNode.SetName(f"{caseId}_results")
                loadedNodes["table"] = tableNode

                selectionNode = (
                    slicer.app.applicationLogic().GetSelectionNode()
                )
                selectionNode.SetReferenceActiveTableID(tableNode.GetID())
                slicer.app.applicationLogic().PropagateTableSelection()

                slicer.util.selectModule("Tables")

                self.log(f"Loaded table: {csvPath}")
            else:
                self.log("Results table CSV not found.")

        elif loadTable and not distancesWereCalculated:
            self.log("")
            self.log("=== Loading results table ===")
            self.log(
                "Skipped because thickness measurements were not calculated."
            )

        self.log("")
        self.log("=== Finished ===")

        return result, loadedNodes